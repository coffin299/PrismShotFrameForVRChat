// SPDX-License-Identifier: Apache-2.0
// TODO(要確認): アバターに付けたカメラの _CameraDepthTexture が、そのカメラ自身の深度か。
Shader "PrismShot/DepthEncode"
{
    Properties
    {
        _NearMeters ("Near Meters", Float) = 0.3
        _FarMeters ("Far Meters", Float) = 10
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "VRCFallback"="Hidden" }
        Cull Off
        ZWrite Off
        ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            // このカメラが作った深度を読む。
            UNITY_DECLARE_DEPTH_TEXTURE(_CameraDepthTexture);
            float _NearMeters;
            float _FarMeters;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float4 screenPos : TEXCOORD0;
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                // 板を画面いっぱいに出す。深度のサンプル位置はスクリーン座標。
                o.pos = UnityObjectToClipPos(v.vertex);
                o.screenPos = ComputeScreenPos(o.pos);
                return o;
            }

            float4 frag(v2f i) : SV_Target
            {
                float2 uv = i.screenPos.xy / max(i.screenPos.w, 0.0001);
                float raw = SAMPLE_DEPTH_TEXTURE(_CameraDepthTexture, uv);
                // 視点からのメートル距離にして、近い距離と遠い距離の間へ収める。
                float eye = LinearEyeDepth(raw);
                float span = max(_FarMeters - _NearMeters, 0.001);
                float far01 = saturate((eye - _NearMeters) / span);
                // 近いほど白なので、遠い側の 1 を反転する。
                float nearWhite = 1.0 - far01;
                uint packed = (uint)round(nearWhite * 65535.0);
                float high = ((packed >> 8) & 255) / 255.0;
                float low = (packed & 255) / 255.0;
                return float4(high, low, 0.0, 1.0);
            }
            ENDCG
        }
    }
}
