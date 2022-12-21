# This code is provided to you by UAB CGTrader, code 302935696, address - Antakalnio str. 17,
# Vilnius, Lithuania, the company registered with the Register of Legal Entities of the Republic
# of Lithuania (CGTrader).
#
# Copyright (C) 2022  CGTrader.
#
# This program is provided to you as free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version. It is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public License along with this
# program. If not, see https://www.gnu.org/licenses/.

"""
Blender specific animation functionality
"""

import math

import threed.blender.common


def is_object_animated(object):
    """
    Returns whether the object can be considered animated.
    """

    if not (object.animation_data and object.animation_data.action):
        return False

    for fc in object.animation_data.action.fcurves:
        if not fc.is_empty:
            return True

    return False


def move_animated(object, offset):
    """
    Applies translation to an animated object, adjusting its location tracks.
    If NLA tracks are used instead of action, it will update the topmost NLA track.
    Offset values must be in parent space (for a top-level object this will be world space.
    """

    if object.animation_data is None:
        object.location += offset

    else:
        action = (
            object.animation_data.action
            or (object.animation_data.nla_tracks
                and object.animation_data.nla_tracks[-1].strips[0].action)
            or None
        )
        if action is None:
            return

        gen_location_curves = (c for c in action.fcurves if c.data_path == 'location')
        for v, curve in zip(offset, gen_location_curves):
            if curve.is_empty:
                curve.keyframe_points.insert(0, v)
            else:
                for p in curve.keyframe_points:
                    p.co[1] += v
                    p.handle_left[1] += v
                    p.handle_right[1] += v


def get_activity_ranges(objects, threshold=0.001, start=0, end=250):
    """
    Returns a list of 2-element tuples, each denoting time ranges
    where the objects' properties were changing.

    Args:
        objects (object[]): objects to evaluate
        threshold (float):  minimal rate of change between frames to count as "active"
        start (int):        frame to start evaluating from
        end (int):          frame to start evaluating with

    Return:
        list of int-tuple[2], ranges in ascending order, guaranteed non-overlapping
    """

    allcurves = []
    for obj in objects:
        if is_object_animated(obj):
            allcurves.extend(obj.animation_data.action.fcurves)

    ranges = []
    last_values = [fc.evaluate(start - 1) for fc in allcurves]
    range_start = None
    for t in range(start, end):
        is_change = False
        for i, fc in enumerate(allcurves):
            cur_val = fc.evaluate(t)
            if not is_change and math.fabs(cur_val - last_values[i]) > threshold:
                is_change = True
            last_values[i] = cur_val

        if is_change:
            if range_start is None:
                range_start = t - 1
        elif range_start is not None:
            ranges.append((range_start, t - 1))
            range_start = None

    return ranges


def extract_new_action(action, frame_range, name, set_start=None, prevent_empty=True):
    """
    Makes a new action from given one, which only contains animation from given frames.

    NOTE: For now does not insert keyframes at boundaries; if a keyframe is outside of range,
    it will be ignored. This can result in changed animation result on non-baked animation.

    Args:
        action (Action):        original action to extract animation from
        frame_range (tuple[2]): extract animation between these start and end frames (inclusive)
        name (string):          created action's name
        set_start (None|int):   (default None) if supplied, moves animation to start at this frame
        prevent_empty (bool):   Add single keyframe if new action ends up having none,
                                This is to work around NLA track export issue, where empty actions
                                don't contribute towards track merge, and subsequently get exported
                                using action names instead of NLA track names

    Return:
        (Action) new action containing only extracted animation
    """

    new_act = action.copy()
    new_act.name = name

    start_frame, end_frame = frame_range

    for fc in new_act.fcurves:
        fc.update()
        for k in reversed(fc.keyframe_points):
            k_time = k.co[0]
            if k_time < start_frame or k_time > end_frame:
                fc.keyframe_points.remove(k, fast=True)

    if prevent_empty:
        is_act_empty = all((fc.is_empty for fc in new_act.fcurves))
        if is_act_empty:
            for orig_fc, this_fc in zip(action.fcurves, new_act.fcurves):
                value = orig_fc.evaluate(start_frame)
                this_fc.keyframe_points.insert(start_frame, value)

    if set_start is not None:
        offset = set_start - start_frame
        for fc in new_act.fcurves:
            for k in fc.keyframe_points:
                k.co[0] += offset
                k.handle_left[0] += offset
                k.handle_right[0] += offset

    for fc in new_act.fcurves:
        fc.update()

    return new_act


def publish_to_nla(object, action, name=None):
    """
    Adds NLA track for supplied action.
    If `name` is not supplied, the track name will attempt to match action name.
    """

    track = object.animation_data.nla_tracks.new()
    track.name = name or action.name
    strip = track.strips.new(name, 0, action)
    strip.name = name

    return track


def make_clip(objects, clip_name, clip_range, use_nla=True):
    """
    Creates a single clip for given objects.
    Expects all supplied objects to be animated.
    """

    is_solo = len(objects) == 1
    new_actions = []
    for obj in objects:
        act_name = clip_name if is_solo else "{}_{}".format(clip_name, obj.name)
        clip_act = extract_new_action(
            obj.animation_data.action, clip_range, act_name, set_start=0
        )

        if use_nla:
            publish_to_nla(obj, clip_act, name=clip_name)

        new_actions.append(clip_act)

    return new_actions


def setup_object_clips(objects, clips, animated_only=True, use_nla=True, **kwargs):
    """
    Sets up clips for given objects.

    Args:
        objects (Object):       list of objects to create clips for
        clips (dict):           each animation is passed as "animation_name": (<start>, <end>)
        animated_only (bool):   if True (default) will skip objects without animation,
                                otherwise will setup static animation for them
        use_nla (bool):         if True (default), will setup created clips as NLA tracks
        **kwags:                Any additional keyword arguments are used to insert values into
                                clip names of the form {name}. E.g.: clip name "prefix_{value}"
                                and arg value="foo" will result in animation name "prefix_foo".

    Returns:
        (dict) where key is local clip name, and contents is a list of created actions
    """

    if animated_only:
        activities = get_activity_ranges(objects)

    new_actions = {}
    for clip_name, (clip_start, clip_end) in clips.items():
        if animated_only:
            overlap = False
            for start, end in activities:
                if start <= clip_end and clip_start <= end:
                    overlap = True

            if not overlap:
                continue

        clip_name_local = clip_name.format(**kwargs)
        actions = make_clip(objects, clip_name_local, (clip_start, clip_end), use_nla=use_nla)

        new_actions[clip_name_local] = actions

    return new_actions


def setup_clips(
    objects,
    global_clips={"static_animation": (0, 1)},
    root_clips={
        "hotspot_{rootname}_0": (1, 51),
        "hotspot_{rootname}_1": (52, 102),
    },
    local_clips={},
    use_nla=True,
):
    """
    Splits animation into multiple actions, and optionally adds them in NLA for export.
    The animated objects MUST have animation ranges enought for specified animations.
    Note: non-animated objects are skipped.

    Args:
        objects (object[]):  scene objects to process for
        *_clips (dict):      each animation is passed as "animation_name": (<start>, <end>)
                             some replacable values are available:
                                {rootname} - name of the topmost parent for a given object
                                {objectname}  - name of current object
                             Note that without distinguishing names using replaceables,
                             The animations will behave as if passed global_clips.
        global_clips (dict): clips applied as shared by all objects
        root_clips (dict):   clips applied as shared by children of each top level parent
        local_clips (dict):  clips applied as unique to each animated object
        use_nla (bool):      if True (default), will setup created clips as NLA tracks
    """

    anim_objects = [obj for obj in objects if is_object_animated(obj)]
    new_actions = {'global': {}, 'rooted': {}, 'local': {}}

    root_groups = threed.blender.common.sort_by_hierarchy(anim_objects, add_children=False)
    for group in root_groups:
        new_actions['rooted'].update(
            setup_object_clips(
                group, root_clips, use_nla=use_nla, rootname=group[0].name
            )
        )

    for obj in anim_objects:
        new_actions['local'].update(
            setup_object_clips(
                (obj,), local_clips, use_nla=use_nla, objectname=obj.name
            )
        )

    for clip_name, clip_range in global_clips.items():
        actions = make_clip(anim_objects, clip_name, clip_range, use_nla=use_nla)
        new_actions['global'][clip_name] = actions

    if use_nla:
        for obj in anim_objects:
            obj.animation_data.action = None

    return new_actions
