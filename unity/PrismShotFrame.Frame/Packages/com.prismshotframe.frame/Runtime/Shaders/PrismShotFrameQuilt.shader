// SPDX-License-Identifier: Apache-2.0
// TODO(要確認): VRChat のシングルパスステレオで、_WorldSpaceCameraPos が目ごとに分かれるか。
Shader "PrismShotFrame/Quilt"
{
    Properties
    {
        _MainTex ("Quilt", 2D) = "black" {}
        _Columns ("Columns", Float) = 8
        _Rows ("Rows", Float) = 6
        _ViewCount ("View Count", Float) = 48
        _MaxAngle ("Max Angle", Float) = 0.45
        _Focus ("Focus", Float) = 0.5
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "VRCFallback"="Unlit" }
        Cull Back
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float _Columns;
            float _Rows;
            float _ViewCount;
            float _MaxAngle;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.texcoord;
                return o;
            }

            float2 TileUv(int index, float2 uv, float columns, float rows)
            {
                int cols = (int)columns;
                int x = index % cols;
                int y = index / cols;
                // 視点0はテクスチャの下段。Unity の UV も下が 0。
                return float2((x + uv.x) / columns, (y + uv.y) / rows);
            }

            float4 frag(v2f i) : SV_Target
            {
                float3 center = mul(unity_ObjectToWorld, float4(0, 0, 0, 1)).xyz;
                float3 right = normalize(mul((float3x3)unity_ObjectToWorld, float3(1, 0, 0)));
                float3 forward = normalize(mul((float3x3)unity_ObjectToWorld, float3(0, 0, 1)));
                float3 toCam = _WorldSpaceCameraPos - center;
                // 右にいる人ほど、右端の視点を選ぶ。
                float angle = atan2(dot(toCam, right), max(dot(toCam, forward), 0.001));
                float span = max(_MaxAngle, 0.001);
                float t = saturate(0.5 + angle / (2.0 * span));
                float count = max(_ViewCount, 1.0);
                float columns = max(_Columns, 1.0);
                float rows = max(_Rows, 1.0);
                float viewF = t * (count - 1.0);
                int view0 = (int)floor(viewF);
                int view1 = min(view0 + 1, (int)count - 1);
                float blend = frac(viewF);
                float4 a = tex2D(_MainTex, TileUv(view0, i.uv, columns, rows));
                float4 b = tex2D(_MainTex, TileUv(view1, i.uv, columns, rows));
                return lerp(a, b, blend);
            }
            ENDCG
        }
    }
}
