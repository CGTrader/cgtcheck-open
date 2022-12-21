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
Common functionality for generic tests
"""
import os
import sys
from pathlib import Path
from base64 import b85decode
from zlib import decompress


import pytest
from PIL import Image


def is_compatible_blender() -> bool:
    """
    Returns True if code is running in compatible Blender.
    """

    if not os.path.basename(sys.argv[0]).lower() in ('blender', 'blender.exe'):
        return False

    try:
        import bpy
    except (ModuleNotFoundError, ImportError):
        return False

    return True


def is_compatible_3dsmax() -> bool:
    """
    Returns True if code is running in compatible 3dsmax.
    """

    if not os.path.basename(sys.executable).lower() in ('3dsmax.exe', '3dsmaxio.exe'):
        return False

    try:
        from pymxs import runtime as rt
    except (ModuleNotFoundError, ImportError):
        return False

    try:
        if not rt.maxOps.productAppID == rt.Name('max'):
            return False

    except (AttributeError, TypeError):
        return False

    return True


@pytest.fixture
def create_texture_aspect_ratio_correct(tmpdir: str) -> Path:
    """
    Creates a texture with the correct aspect ratio.
    """
    img = Image.new('RGB', (25, 25), color='white')
    texture_path = Path(tmpdir) / 'texture_aspect_ratio_correct.png'
    img.save(texture_path)
    yield texture_path


@pytest.fixture
def create_texture_with_incorrect_name(tmpdir: str) -> Path:
    """
    Creates a texture with incorrect name
    """
    img = Image.new('RGB', (1, 1), color='white')
    texture_path = os.path.join(tmpdir, 'textureName.png')
    img.save(texture_path)
    yield texture_path


@pytest.fixture
def create_texture_aspect_ratio_wrong(tmpdir: str) -> Path:
    """
    Creates a texture with the wrong aspect ratio.
    """
    texture_path = Path(tmpdir) / 'texture_aspect_ratio_wrong.png'
    img = Image.new('RGB', (50, 25), color='white')
    img.save(texture_path)
    yield texture_path


@pytest.fixture
def indexed_colors_image(tmpdir) -> str:
    texture_path = os.path.join(tmpdir, 'indexed_colors_texture.png')

    img = Image.new('RGB', (4, 4), color='white')
    img = img.convert("P", palette=Image.ADAPTIVE, colors=16)
    img.save(texture_path)

    return texture_path


@pytest.fixture
def non_indexed_colors_image(tmpdir) -> str:
    texture_path = os.path.join(tmpdir, 'non_indexed_colors_texture.png')

    img = Image.new('RGB', (4, 4), color='white')
    img.save(texture_path)

    return texture_path


@pytest.fixture
def textures_with_res(tmpdir: pytest.fixture, request: pytest.fixture) -> str:

    texture_paths = []

    for texture_id, resolution in enumerate(request.param, start=1):
        texture_path = os.path.join(tmpdir, 'texture_{}.png'.format(texture_id))
        width, height = resolution
        img = Image.new('RGB', (width, height), color='white')
        img.save(texture_path)
        texture_paths.append(texture_path)

    return texture_paths


@pytest.fixture
def textures_with_mat_name_and_types(tmpdir: pytest.fixture, request: pytest.fixture) -> str:

    texture_paths = []

    for mat_name, texture_types in request.param.items():
        for texture_type in texture_types:
            texture_path = os.path.join(tmpdir, '{}_{}.png'.format(mat_name, texture_type))
            img = Image.new('RGB', (1, 1), color='white')
            img.save(texture_path)
            texture_paths.append(texture_path)

    return texture_paths


@pytest.fixture
def file_on_top_of_multiple_formats_textures_hierarchy(
    tmpdir: pytest.fixture, request: pytest.fixture
) -> str:
    for texture_subpath in request.param:
        path = os.path.join(tmpdir, texture_subpath)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        img = Image.new('RGB', (5, 5), color='white')
        img.save(path)

    input_file_path = os.path.join(tmpdir, 'input.txt')
    open(input_file_path, 'a').close()

    return input_file_path


@pytest.fixture
def textures_with_mode(tmpdir: pytest.fixture, request: pytest.fixture) -> str:
    texture_paths = []
    for texture_name, mode in request.param:
        texture_path = os.path.join(tmpdir, texture_name)

        img = Image.new(mode, (5, 5), color='white')
        img.save(texture_path)
        texture_paths.append(texture_path)

    return texture_paths


@pytest.fixture
def arithmetic_coded_jpg(tmpdir: pytest.fixture) -> str:
    content = b85decode(b'|JeWF01!$>Nk#wx0RaF=07w7;|JwjV00RO70|EjA0|NsD0|NvF2n7WM1O*BQ2L=cX3JeSj3JVJj4iXRz4iOFu3lJ6%5fc;@6%`B*7Z?^47!ni}6#v@*LjeN>1O)^I2?YfS6b%av6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6ciK`6cqo-01*fPKmb4k0TBQK5di}c0sqVZ3IGrg1pyEd1^?Or3<CiG0ucid06zf#0Mh58Nw6VRRVX~fbZs(nXSw(*bGzC90L=B=zBkLaeu!9+0VUUe51SK^0kFL-n+q6ehaUv2$J5`>@H|^sygLhk{{Z0vAr@6eDPSBAebOUQO4N=lBQXgb@xWK`ohu&u*fF;q<n~Fq&QjWoXg!crb;ap`R|o8YoK_*pH)~)H%t~%>y71@RrZr+`IZ`}4{SGv^W)7k%sWypY9jj0+k8$X)eaddnP9_z^84aKSSRQ?<*rARf;2ZD9V%(L;a2`KEzRx7F2aMd7NY|-<ra%eufe-pYjQ;@f-nXIRbOj*nHIN8E{{Z*!@~Lw|aQQ-Zwyr1kK?T&|4*FMp%2u{ux8Zr?OuAzLD+<Lvg&3&FzkYI^hzny*y?=mc>H+sSAq)$1_PumQ^~{)5a^VUDNJ~uLny&Pq%o-z`xv~73LGXLd4#zV3Y0F#4q#c`Ktrho5Mm{a`SRs0_YS@Pp1LjlS0#;luM(mRkC$s1pqm7yk;h%Lo)1S9H5RQacT|Cw8-ZHZ3X^M7@`VXNBK&tjBkzB_D*42vYU@T_}Z4M18Z9J&te|6g}$}_WlvFm~r43UdH%tn#<n<V9}GRs3F^dgt-pd2c>PO_efrIzY`?Q<i%x~$=o68``e%x6*F*bsU^nfpTp7LdyrLzn09vH7M|mmH{@O}coDu9W!^#-r}tKk{;^;Oi*}xzJDG-W}d@&yQp^{JyWRycu_)<t%9w&Er+enQ>HlVXf-|F&Pw=O38s=%QlgzI7Om#qmYtY?KLE(+`Xe<_ueY)4`1){%no!4Yihi6$45=sC2`EJ{{YL#+NNf=43PdOZ|`sqK%hVxOw5-9t(o`({W6+?T|fEgmwj#)#AIqd4th~tUAqNOonNWb4VRL8L!<FKxhYr8)cKw&AKjFj5+t*O!9wS^vHfH|nxjcg^}jGUs*D7KU%E}tcz9{*q(bc8^q-?PS9JsJXws1S0wc;I*at%NrWwA#^9_M9K;zt#U70gr#hxuad<y|aIUbjyzU(jzI=hs2i8P$c-Ys}aq6A2ZDaxTxU^qc_&8?b1G=fEl9<nRMES_m>^!K(P+KS#QcDwnHtrXyAN@#{7QH)am0P6AC%u)1r_c8J@evn`(2tBgxf?2;5zACJZ{A&LIBNYZ>U^db#C<>c6j|8X5j9hn_ug8rkb;ZLGa7}E2L0tRqMQ-(x8(@_Fs{s;kKt9%e7#<nbDbCk*q#`sOb%)gBqz#fiBoYt1ZR}uc0<HJgDqQ#~%YWfnQ;l+svaEc6xna+6f`E=Y_IVC^yipMh@CHv$?abLv4i{YwoMtdTW~kCRGjs{XZL}TSBOANvcCvQP4m0gLjz%Olk0TRjNVfDofTc68La2wRgaI_CO#uirYFE+N6`br@ZOua-n1}rjrD@vi?y9uA&B50X&Z`d~WW%;1GJUCY2hYUq!1GfU?hwq((k9RF4}Ur#xkADhuvb8v`Vlu7b{obv*lmshoBsgV596a#d#xqxcYvG313Tfn{0_ci0Ff>K0PE~4{feepDv+wSqBl#8RS4-7^{Z*-q+}^DVfHYE{g?H{8}i$AspXf;dkeR^TqQ^9{mBF9M33WvCe;lO%r~VR^4lcUrcmPPXt1%$@}*E3)oKoOi(%6l&TA}A=zfT3>(PH!jxLaShJkG4qf-86<@%ZrwsY_3!oGu~Uamde`X!;c%X_(VOr6J>sdx^MVBb7X<I#mz*%qFnfsHSbYPQXgzx<83e0w6MofCKBS(bmxn<YWk_{t2B3zk_DzeBPnJ429YIK!6VFv!jS00y(fxxY)G1^wT@WVdZ@#u4A&N4^QcTJjvXE?7Gzv~d5~')  # noqa E501

    texture_path = os.path.join(tmpdir, 'arithmetic_coded.jpg')
    with open(texture_path, 'wb') as f:
        f.write(content)

    return texture_path


@pytest.fixture
def bmp_with_unsupported_compression(tmpdir: pytest.fixture) -> str:
    content = decompress(b85decode(b'c${<c-N3>C23<h921v6(F(U&95Hm2S0kIG_1cL=YnBhMRfjLg@LB$P+zG@`wkP}sCea+}#Y%JW6mZs*Amd3VV=1fi-uItPyG5tmiNPvX_6a4@GAB;!AC>RAJ3$QUV5hNKH0V~=X`2'))  # noqa #501

    texture_path = os.path.join(tmpdir, 'unsupported_compression.bmp')
    with open(texture_path, 'wb') as f:
        f.write(content)

    return texture_path


@pytest.fixture
def default_fbx_binary_file(tmpdir: pytest.fixture) -> str:
    content = decompress(b85decode(b'c$~#oUu+ab7~lT6-nG4}fC36=&jgX8ZLgpL#t7||gH3yF(``}F#7y_*+J(K{%j|4z6C^Pv#s`fiCdPyZjBm!EsL>}Ajq=b3|HYW7FFdFiNPWNuq7f4PzL~x5EZ1!j9-QoLXXpFA-}iUEnGTWp5@94;7<fE8U^#@%XS3QS?ZOsK8%t_SV;#^BQBtDpz#ONJXSvQ(u-pK@1pL-4kq=XbM18SI)8-V8HsGky5c~~=)^Wfw*?g4)ZDPJkbyWCVL#TXho>3yGR)rdzRI1-7(#a)QP<dV<G(SNJ(|-dmt}3gEqU-P(y%ljA!sVtxGOurd$-T;A^C8z~dKzZ?l+~7^<@lTm?#I-1gPN{W(mP?!mG$<bW!sh~iQhG8(Q!85>_u0Eqb@Ucz{h}19SCT4yT{3tO+|+E(XMQFc4yDtT|Ip{m_5+56J~jEu@Oy&U#nqKhw4t*HP*xDLED`oHhyXiAteQrNsqEY!bxYN)Sp3rG5itgp2lSYU4oC4;zz1TIYI7n9QU&dAu(Zbn;Iziy2@|(Q%9-E1>s$V(9-Yo8Hfq4FDUD&Av*tz%SxW0{H#*O>8ypi1?7sWB=1%#)R9Ue;~}Nk(__r7QpPRn?as|KNzuJnLt{oe{26pjA5kWmZJ^kY!I|Yu8yFH?Lkz*#TXrG*tfxFR_dx*jh=l1t7G~ZE(yu^lhNZ0%39~iItZCT0w)g-StFG^qq%gi7ZI-%+rNkyh;&^|xYFnn*U5BCGAkL~COAy97r6LOmFGNlT$fFYZ_88<50{eD(+>P;-z8HWHNbt?EW{WzD!N=8LzZ4P@uPE`>t9Veo6uZmQ2a6LTinWDnOwIN6!qc~RcP^XDJuIG{TrT%&B9h&;Ds;iJ=?Ve3Cc9rGWOnb7NZ6)^iN_5xOG`27y{jeS*Jf4ZCi8ndfF6_3cf>*8Sc1O_(DM>~OT6LNnc=Ra1RRlo8zO)=nPTnw##~Z%8?3GtOub$jUjy^)AMRNEc<Yy+f4XpH$J_T^{o{1Nhfb#>=NsC9+Piao@MQY}8{o-ZO5XHY;iN-bJLKtLP|hKw-quvip-L2)NN?mR$=xO64e8V-tNnA9CmNUqeHN3WJDg5a*}!#F@LnL+EydbGF>BgcS@dEcdVjb*3JebPm6eLau~kauq+}){xvE~$TBkSf!r`;BUVNRZ*BeT%s`p$V-KQ-b8@0x=TBQGhad(>(e^83As~2C@g6RNakA%1dljT_4Fo{hI#Ka23yq8=b3QtT&{K`~-Fer=W(!P%Zl>HKAqiV>1M{9?siN+q1Xjq>8l_?7j(!6T}gzS?r8$UQ;Bx)Zj#&VM*?b62nFjIrHOnjT?p}jE@(|>M*7i@}>Z^8x~gKblVTZ}bJUk>1cPL4L={w}&DYG8+_j$a93bUX*X4n%f^7KoNmB@SGB85h0`iKXTm4TXnmE_9?Nz|Jr*A%I(rl|S>th0kysPNeISo%cQNRtgM4Fb)lK_4Mr7uf>ixGvU0ocKPv6rj^@a9u6NaD(^L5#?rhKeyJMs@LL0Jr-&MIiz{t7n^E8+jcQXyo~qlzxEOG?H|eOnbD}41c>NTwCo_>`+=`VU65H=s6-bA9Y=u*=&hr;C(nstZsd3lkBTxs!b!>Ixtm0DJI4x5~9g}(yp6QNo-VP;e!H$C7?Oo2qT*uQL%Le>Nu#B#@$;gO*2oOGcR1}v7h#xO1CMG3x)Q8im4|&&da1((K5vKDBQ(}S~qu!5-A<4YY*s_=V$oTt{cUr$)_`dx9?3L%Y{JHH!l#2hG{$Jy-BQG62cloCizh6xM;=j_>{x4KN@aF'))  # noqa #501

    filepath = os.path.join(tmpdir, 'default_fbx_binary_file.fbx')
    with open(filepath, 'wb') as f:
        f.write(content)

    return filepath


fbx_ascii_content = """; FBX 7.7.0 project file
; ----------------------------------------------------

FBXHeaderExtension:  {
	FBXHeaderVersion: 1004
	FBXVersion: 7700
	CreationTimeStamp:  {
		Version: 1000
		Year: 2022
		Month: 9
		Day: 15
		Hour: 12
		Minute: 10
		Second: 47
		Millisecond: 752
	}
	Creator: "FBX SDK/FBX Plugins version 2020.3.2"
	OtherFlags:  {
		TCDefinition: 127
	}
	SceneInfo: "SceneInfo::GlobalInfo", "UserData" {
		Type: "UserData"
		Version: 100
		MetaData:  {
			Version: 100
			Title: ""
			Subject: ""
			Author: ""
			Keywords: ""
			Revision: ""
			Comment: ""
		}
		Properties70:  {
			P: "DocumentUrl", "KString", "Url", "", "C:\tmp\tmp_ascii.fbx"
			P: "SrcDocumentUrl", "KString", "Url", "", "C:\tmp\tmp_ascii.fbx"
			P: "Original", "Compound", "", ""
			P: "Original|ApplicationVendor", "KString", "", "", "Blender Foundation"
			P: "Original|ApplicationName", "KString", "", "", "Blender (stable FBX IO)"
			P: "Original|ApplicationVersion", "KString", "", "", "2.93.10"
			P: "Original|DateTime_GMT", "DateTime", "", "", "01/01/1970 00:00:00.000"
			P: "Original|FileName", "KString", "", "", "/foobar.fbx"
			P: "LastSaved", "Compound", "", ""
			P: "LastSaved|ApplicationVendor", "KString", "", "", "Blender Foundation"
			P: "LastSaved|ApplicationName", "KString", "", "", "Blender (stable FBX IO)"
			P: "LastSaved|ApplicationVersion", "KString", "", "", "2.93.10"
			P: "LastSaved|DateTime_GMT", "DateTime", "", "", "01/01/1970 00:00:00.000"
		}
	}
}
GlobalSettings:  {
	Version: 1000
	Properties70:  {
		P: "UpAxis", "int", "Integer", "",1
		P: "UpAxisSign", "int", "Integer", "",1
		P: "FrontAxis", "int", "Integer", "",2
		P: "FrontAxisSign", "int", "Integer", "",1
		P: "CoordAxis", "int", "Integer", "",0
		P: "CoordAxisSign", "int", "Integer", "",1
		P: "OriginalUpAxis", "int", "Integer", "",-1
		P: "OriginalUpAxisSign", "int", "Integer", "",1
		P: "UnitScaleFactor", "double", "Number", "",1
		P: "OriginalUnitScaleFactor", "double", "Number", "",1
		P: "AmbientColor", "ColorRGB", "Color", "",0,0,0
		P: "DefaultCamera", "KString", "", "", "Producer Perspective"
		P: "TimeMode", "enum", "", "",11
		P: "TimeProtocol", "enum", "", "",2
		P: "SnapOnFrameMode", "enum", "", "",0
		P: "TimeSpanStart", "KTime", "Time", "",0
		P: "TimeSpanStop", "KTime", "Time", "",46186158000
		P: "CustomFrameRate", "double", "Number", "",24
		P: "TimeMarker", "Compound", "", ""
		P: "CurrentTimeMarker", "int", "Integer", "",-1
	}
}

; Documents Description
;------------------------------------------------------------------

Documents:  {
	Count: 1
	Document: 2105583884896, "Scene", "Scene" {
		Properties70:  {
			P: "SourceObject", "object", "", ""
			P: "ActiveAnimStackName", "KString", "", "", ""
		}
		RootNode: 0
	}
}

; Document References
;------------------------------------------------------------------

References:  {
}

; Object definitions
;------------------------------------------------------------------

Definitions:  {
	Version: 100
	Count: 3
	ObjectType: "GlobalSettings" {
		Count: 1
	}
	ObjectType: "Model" {
		Count: 1
		PropertyTemplate: "FbxNode" {
			Properties70:  {
				P: "QuaternionInterpolate", "enum", "", "",0
				P: "RotationOffset", "Vector3D", "Vector", "",0,0,0
				P: "RotationPivot", "Vector3D", "Vector", "",0,0,0
				P: "ScalingOffset", "Vector3D", "Vector", "",0,0,0
				P: "ScalingPivot", "Vector3D", "Vector", "",0,0,0
				P: "TranslationActive", "bool", "", "",0
				P: "TranslationMin", "Vector3D", "Vector", "",0,0,0
				P: "TranslationMax", "Vector3D", "Vector", "",0,0,0
				P: "TranslationMinX", "bool", "", "",0
				P: "TranslationMinY", "bool", "", "",0
				P: "TranslationMinZ", "bool", "", "",0
				P: "TranslationMaxX", "bool", "", "",0
				P: "TranslationMaxY", "bool", "", "",0
				P: "TranslationMaxZ", "bool", "", "",0
				P: "RotationOrder", "enum", "", "",0
				P: "RotationSpaceForLimitOnly", "bool", "", "",0
				P: "RotationStiffnessX", "double", "Number", "",0
				P: "RotationStiffnessY", "double", "Number", "",0
				P: "RotationStiffnessZ", "double", "Number", "",0
				P: "AxisLen", "double", "Number", "",10
				P: "PreRotation", "Vector3D", "Vector", "",0,0,0
				P: "PostRotation", "Vector3D", "Vector", "",0,0,0
				P: "RotationActive", "bool", "", "",0
				P: "RotationMin", "Vector3D", "Vector", "",0,0,0
				P: "RotationMax", "Vector3D", "Vector", "",0,0,0
				P: "RotationMinX", "bool", "", "",0
				P: "RotationMinY", "bool", "", "",0
				P: "RotationMinZ", "bool", "", "",0
				P: "RotationMaxX", "bool", "", "",0
				P: "RotationMaxY", "bool", "", "",0
				P: "RotationMaxZ", "bool", "", "",0
				P: "InheritType", "enum", "", "",0
				P: "ScalingActive", "bool", "", "",0
				P: "ScalingMin", "Vector3D", "Vector", "",0,0,0
				P: "ScalingMax", "Vector3D", "Vector", "",1,1,1
				P: "ScalingMinX", "bool", "", "",0
				P: "ScalingMinY", "bool", "", "",0
				P: "ScalingMinZ", "bool", "", "",0
				P: "ScalingMaxX", "bool", "", "",0
				P: "ScalingMaxY", "bool", "", "",0
				P: "ScalingMaxZ", "bool", "", "",0
				P: "GeometricTranslation", "Vector3D", "Vector", "",0,0,0
				P: "GeometricRotation", "Vector3D", "Vector", "",0,0,0
				P: "GeometricScaling", "Vector3D", "Vector", "",1,1,1
				P: "MinDampRangeX", "double", "Number", "",0
				P: "MinDampRangeY", "double", "Number", "",0
				P: "MinDampRangeZ", "double", "Number", "",0
				P: "MaxDampRangeX", "double", "Number", "",0
				P: "MaxDampRangeY", "double", "Number", "",0
				P: "MaxDampRangeZ", "double", "Number", "",0
				P: "MinDampStrengthX", "double", "Number", "",0
				P: "MinDampStrengthY", "double", "Number", "",0
				P: "MinDampStrengthZ", "double", "Number", "",0
				P: "MaxDampStrengthX", "double", "Number", "",0
				P: "MaxDampStrengthY", "double", "Number", "",0
				P: "MaxDampStrengthZ", "double", "Number", "",0
				P: "PreferedAngleX", "double", "Number", "",0
				P: "PreferedAngleY", "double", "Number", "",0
				P: "PreferedAngleZ", "double", "Number", "",0
				P: "LookAtProperty", "object", "", ""
				P: "UpVectorProperty", "object", "", ""
				P: "Show", "bool", "", "",1
				P: "NegativePercentShapeSupport", "bool", "", "",1
				P: "DefaultAttributeIndex", "int", "Integer", "",-1
				P: "Freeze", "bool", "", "",0
				P: "LODBox", "bool", "", "",0
				P: "Lcl Translation", "Lcl Translation", "", "A",0,0,0
				P: "Lcl Rotation", "Lcl Rotation", "", "A",0,0,0
				P: "Lcl Scaling", "Lcl Scaling", "", "A",1,1,1
				P: "Visibility", "Visibility", "", "A",1
				P: "Visibility Inheritance", "Visibility Inheritance", "", "",1
			}
		}
	}
	ObjectType: "Geometry" {
		Count: 1
		PropertyTemplate: "FbxMesh" {
			Properties70:  {
				P: "Color", "ColorRGB", "Color", "",0.8,0.8,0.8
				P: "BBoxMin", "Vector3D", "Vector", "",0,0,0
				P: "BBoxMax", "Vector3D", "Vector", "",0,0,0
				P: "Primary Visibility", "bool", "", "",1
				P: "Casts Shadows", "bool", "", "",1
				P: "Receive Shadows", "bool", "", "",1
			}
		}
	}
}

; Object properties
;------------------------------------------------------------------

Objects:  {
	Geometry: 2105584117792, "Geometry::Cube.001", "Mesh" {
		Vertices: *24 {
			a: -1,-1,-1,-1,-1,1,-1,1,-1,-1,1,1,1,-1,-1,1,-1,1,1,1,-1,1,1,1
		}
		PolygonVertexIndex: *24 {
			a: 0,1,3,-3,2,3,7,-7,6,7,5,-5,4,5,1,-1,2,6,4,-1,7,3,1,-6
		}
		Edges: *12 {
			a: 0,1,2,3,5,6,7,9,10,11,13,15
		}
		GeometryVersion: 124
		LayerElementNormal: 0 {
			Version: 102
			Name: ""
			MappingInformationType: "ByPolygonVertex"
			ReferenceInformationType: "Direct"
			Normals: *72 {
				a: -1,0,0,-1,0,0,-1,0,0,-1,0,0,0,1,0,0,1,0,0,1,0,0,1,0,1,0,0,1,0,0,1,0,0,1,0,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,1,0,0,1,0,0,1,0,0,1
			}
			NormalsW: *24 {
				a: 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
			}
		}
		LayerElementUV: 0 {
			Version: 101
			Name: "UVMap"
			MappingInformationType: "ByPolygonVertex"
			ReferenceInformationType: "IndexToDirect"
			UV: *28 {
				a: 0.125,0.75,0.625,0,0.875,0.75,0.375,0.75,0.625,0.25,0.625,1,0.625,0.75,0.375,0.25,0.625,0.5,0.375,1,0.125,0.5,0.875,0.5,0.375,0,0.375,0.5
			}
			UVIndex: *24 {
				a: 12,1,4,7,7,4,8,13,13,8,6,3,3,6,5,9,10,13,3,0,8,11,2,6
			}
		}
		Layer: 0 {
			Version: 100
			LayerElement:  {
				Type: "LayerElementNormal"
				TypedIndex: 0
			}
			LayerElement:  {
				Type: "LayerElementUV"
				TypedIndex: 0
			}
		}
	}
	Model: 2105584138672, "Model::Cube", "Mesh" {
		Version: 232
		Properties70:  {
			P: "InheritType", "enum", "", "",1
			P: "DefaultAttributeIndex", "int", "Integer", "",0
			P: "Lcl Rotation", "Lcl Rotation", "", "A",-90.0000093346673,0,0
			P: "Lcl Scaling", "Lcl Scaling", "", "A",100,100,100
		}
		Culling: "CullingOff"
	}
}

; Object connections
;------------------------------------------------------------------

Connections:  {

	;Model::Cube, Model::RootNode
	C: "OO",2105584138672,0

	;Geometry::Cube.001, Model::Cube
	C: "OO",2105584117792,2105584138672
}
;Takes section
;----------------------------------------------------

Takes:  {
	Current: ""
}
"""  # noqa W191


@pytest.fixture
def default_fbx_ascii_file(tmpdir: pytest.fixture) -> str:
    filepath = os.path.join(tmpdir, 'default_fbx_binary_file.fbx')
    with open(filepath, 'w') as f:
        f.write(fbx_ascii_content)

    return filepath


@pytest.fixture
def call_fixture_scene_with_named_entities(request: pytest.fixture):
    """
    Call scene_with_named_entities based on environment
    """
    if is_compatible_3dsmax():
        from cgtcheck.max.tests.common_max import scene_with_named_entities
    elif is_compatible_blender():
        from cgtcheck.blender.tests.common_blender import scene_with_named_entities

    return scene_with_named_entities(request.param)
