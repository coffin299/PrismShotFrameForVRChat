// SPDX-License-Identifier: Apache-2.0
// TODO(要確認): プロジェクトが Linear 色空間のとき、深度のバイトを正しく戻せるか。
Shader "PrismShotFrame/RGBD"
{
    Properties
    {
        _MainTex ("RGBD", 2D) = "black" {}
        _Strength ("Strength", Float) = 0.03
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
            float _Strength;
            float _Focus;

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

            float SampleDepth(float2 uv)
            {
                float4 packed = tex2D(_MainTex, float2(uv.x * 0.5 + 0.5, uv.y));
                // ガンマ空間では、サンプルがバイト値に近い。
                float high = floor(packed.r * 255.0 + 0.5);
                float low = floor(packed.g * 255.0 + 0.5);
                return (high * 256.0 + low) / 65535.0;
            }

            float4 frag(v2f i) : SV_Target
            {
                float3 center = mul(unity_ObjectToWorld, float4(0, 0, 0, 1)).xyz;
                float3 right = normalize(mul((float3x3)unity_ObjectToWorld, float3(1, 0, 0)));
                float lateral = dot(normalize(_WorldSpaceCameraPos - center), right);
                float depth = SampleDepth(i.uv);
                // 右から見ると、手前が左へ動いて見える。
                float shift = -(depth - _Focus) * _Strength * lateral;
                float2 colorUv = float2(saturate(i.uv.x + shift) * 0.5, i.uv.y);
                return tex2D(_MainTex, colorUv);
            }
            ENDCG
        }
    }
}
