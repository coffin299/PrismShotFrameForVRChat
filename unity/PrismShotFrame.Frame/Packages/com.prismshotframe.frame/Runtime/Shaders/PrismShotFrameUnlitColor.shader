// SPDX-License-Identifier: Apache-2.0
Shader "PrismShotFrame/UnlitColor"
{
    Properties
    {
        _Color ("Color", Color) = (0.2, 0.16, 0.12, 1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "VRCFallback"="Unlit" }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            float4 _Color;

            struct v2f
            {
                float4 pos : SV_POSITION;
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                return o;
            }

            float4 frag(v2f i) : SV_Target
            {
                return _Color;
            }
            ENDCG
        }
    }
}
