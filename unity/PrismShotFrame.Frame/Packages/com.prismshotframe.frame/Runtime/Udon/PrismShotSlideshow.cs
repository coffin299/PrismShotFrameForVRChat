// SPDX-License-Identifier: Apache-2.0
using UdonSharp;
using UnityEngine;

namespace PrismShotFrame
{
    /// <summary>
    /// 額縁の画像を、各クライアントのローカル時間で順番に差し替える。
    /// </summary>
    [UdonBehaviourSyncMode(BehaviourSyncMode.NoVariableSync)]
    public class PrismShotSlideshow : UdonSharpBehaviour
    {
        public Renderer target;
        public Texture[] slides;
        public float intervalSeconds = 5f;
        float _elapsed;
        int _index;

        void Update()
        {
            // 画像が無ければ進めない。
            if (slides == null || slides.Length == 0 || target == null)
            {
                return;
            }
            _elapsed += Time.deltaTime;
            if (_elapsed < intervalSeconds)
            {
                return;
            }
            _elapsed = 0f;
            _index = (_index + 1) % slides.Length;
            Material material = target.material;
            // キルトも RGB-D も _MainTex を絵にする。
            material.SetTexture("_MainTex", slides[_index]);
        }
    }
}
