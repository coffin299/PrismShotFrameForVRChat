// SPDX-License-Identifier: Apache-2.0
using UnityEditor;
using UnityEngine;
using VRC.SDKBase.Editor.BuildPipeline;

namespace PrismShotFrame.Shot.Editor
{
    /// <summary>
    /// Quest と iOS のアバターからは Shot を消す。
    /// TODO(要確認): IVRCSDKPreprocessAvatarCallback が今の SDK でもビルドコピーに対して呼ばれるか。
    /// </summary>
    public sealed class PrismShotQuestStrip : IVRCSDKPreprocessAvatarCallback
    {
        public int callbackOrder => 0;

        public bool OnPreprocessAvatar(GameObject avatarGameObject)
        {
            BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
            // PC 以外のアバターではカメラも独自シェーダーも使えない。
            if (target != BuildTarget.Android && target != BuildTarget.iOS)
            {
                return true;
            }
            PrismShotRoot[] roots = avatarGameObject.GetComponentsInChildren<PrismShotRoot>(true);
            for (int index = 0; index < roots.Length; index++)
            {
                PrismShotRoot root = roots[index];
                // 印をアバターのルートに付けた場合は、アバター自体を消さない。
                if (root == null || root.gameObject == avatarGameObject)
                {
                    continue;
                }
                Object.DestroyImmediate(root.gameObject);
            }
            return true;
        }
    }
}
