// SPDX-License-Identifier: Apache-2.0
// TODO(要確認): 書き出した色がリニア変換で変わると、目印の許容差を超えることがある。
Shader "PrismShot/Composite"
{
    Properties
    {
        _ColorTex ("Color", 2D) = "black" {}
        _DepthTex ("Depth", 2D) = "black" {}
        _NearMeters ("Near Meters", Float) = 0.3
        _FarMeters ("Far Meters", Float) = 10
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "VRCFallback"="Hidden" }
        Cull Back
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _ColorTex;
            sampler2D _DepthTex;
            float _NearMeters;
            float _FarMeters;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                // メッシュの UV は左下が (0, 0)。写真の下端と揃える。
                o.uv = v.texcoord;
                return o;
            }

            void EncodeMeters(float meters, out float high, out float low)
            {
                float encoded = round(max(meters, 0.0) * 100.0);
                high = floor(encoded / 256.0);
                low = encoded - high * 256.0;
            }

            float3 MarkerCell(int index, float nearHigh, float nearLow, float farHigh, float farLow)
            {
                if (index == 0) return float3(80.0, 83.0, 70.0) / 255.0;
                if (index == 1) return float3(nearHigh, nearLow, 170.0) / 255.0;
                if (index == 2) return float3(farHigh, farLow, 85.0) / 255.0;
                return float3(70.0, 83.0, 80.0) / 255.0;
            }

            float4 frag(v2f i) : SV_Target
            {
                float2 uv = i.uv;
                float4 col;
                // 左半分が色、右半分が深度。
                if (uv.x < 0.5)
                {
                    col = tex2D(_ColorTex, float2(uv.x * 2.0, uv.y));
                }
                else
                {
                    col = tex2D(_DepthTex, float2((uv.x - 0.5) * 2.0, uv.y));
                }
                // 横幅 1024 分の 16 を1区画にし、写真いっぱいに写しても目印が残るようにする。
                float cell = 16.0 / 1024.0;
                float nearHigh;
                float nearLow;
                float farHigh;
                float farLow;
                EncodeMeters(_NearMeters, nearHigh, nearLow);
                EncodeMeters(_FarMeters, farHigh, farLow);
                float3 psf = float3(80.0, 83.0, 70.0) / 255.0;
                float3 rev = float3(70.0, 83.0, 80.0) / 255.0;
                if (uv.y < cell && uv.x < cell * 4.0)
                {
                    int index = (int)floor(uv.x / cell);
                    col.rgb = MarkerCell(index, nearHigh, nearLow, farHigh, farLow);
                }
                else if (uv.y < cell && uv.x > 1.0 - cell * 2.0)
                {
                    int which = (int)floor((uv.x - (1.0 - cell * 2.0)) / cell);
                    col.rgb = which == 0 ? psf : rev;
                }
                else if (uv.y > 1.0 - cell && uv.x < cell * 2.0)
                {
                    int which = (int)floor(uv.x / cell);
                    col.rgb = which == 0 ? psf : rev;
                }
                else if (uv.y > 1.0 - cell && uv.x > 1.0 - cell * 2.0)
                {
                    int which = (int)floor((uv.x - (1.0 - cell * 2.0)) / cell);
                    col.rgb = which == 0 ? psf : rev;
                }
                return col;
            }
            ENDCG
        }
    }
}
