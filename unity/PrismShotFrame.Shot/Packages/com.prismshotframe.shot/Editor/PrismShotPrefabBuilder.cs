// SPDX-License-Identifier: Apache-2.0
using System.Collections.Generic;
using System.IO;
using nadena.dev.modular_avatar.core;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using VRC.SDK3.Avatars.Components;
using VRC.SDK3.Avatars.ScriptableObjects;

namespace PrismShotFrame.Shot.Editor
{
    /// <summary>
    /// 手書きの Animator を避け、メニューからプレハブ一式を作る。
    /// TODO(要確認): レイヤー4のカードを、VRChat のメインカメラが描くか。
    /// </summary>
    public static class PrismShotPrefabBuilder
    {
        const string Folder = "Assets/PrismShotFrame/Generated";

        [MenuItem("PrismShot/Build Shot Prefab")]
        public static void Build()
        {
            Shader composite = Shader.Find("PrismShot/Composite");
            Shader depthShader = Shader.Find("PrismShot/DepthEncode");
            Shader preview = Shader.Find("PrismShot/Preview");
            Shader bodyShader = Shader.Find("PrismShot/Body");
            if (composite == null || depthShader == null || preview == null || bodyShader == null)
            {
                EditorUtility.DisplayDialog("PrismShot", "シェーダーが見つかりません。パッケージの導入を確認してください。", "OK");
                return;
            }
            EnsureFolder(Folder);
            RenderTexture colorRt = CreateTarget(Folder + "/PrismShotColor.renderTexture");
            RenderTexture depthRt = CreateTarget(Folder + "/PrismShotDepth.renderTexture");
            Material cardMat = new Material(composite);
            cardMat.SetTexture("_ColorTex", colorRt);
            cardMat.SetTexture("_DepthTex", depthRt);
            cardMat.SetFloat("_NearMeters", 0.3f);
            cardMat.SetFloat("_FarMeters", 10f);
            SaveAsset(cardMat, Folder + "/PrismShotCard.mat");
            Material depthMat = new Material(depthShader);
            depthMat.SetFloat("_NearMeters", 0.3f);
            depthMat.SetFloat("_FarMeters", 10f);
            SaveAsset(depthMat, Folder + "/PrismShotDepth.mat");
            Material previewMat = new Material(preview);
            previewMat.SetTexture("_MainTex", depthRt);
            SaveAsset(previewMat, Folder + "/PrismShotPreview.mat");
            Material bodyMat = new Material(bodyShader);
            bodyMat.color = new Color(0.15f, 0.15f, 0.18f);
            SaveAsset(bodyMat, Folder + "/PrismShotBody.mat");
            AnimatorController controller = BuildController(Folder + "/PrismShot.controller");
            VRCExpressionsMenu menu = BuildMenu(Folder + "/PrismShotMenu.asset");
            GameObject root = BuildHierarchy(colorRt, depthRt, cardMat, depthMat, previewMat, bodyMat, controller, menu);
            // 生成した物体をプレハブにして、シーン上の作業用オブジェクトは消す。
            PrefabUtility.SaveAsPrefabAsset(root, Folder + "/PrismShot.prefab");
            Object.DestroyImmediate(root);
            AssetDatabase.SaveAssets();
            EditorUtility.DisplayDialog("PrismShot", "PrismShot.prefab を作りました。アバターの手の下に置いてください。", "OK");
        }

        static RenderTexture CreateTarget(string path)
        {
            RenderTexture target = new RenderTexture(512, 512, 24, RenderTextureFormat.ARGB32);
            target.name = Path.GetFileNameWithoutExtension(path);
            // 深度のバイトを圧縮で潰さない。
            target.antiAliasing = 1;
            SaveAsset(target, path);
            return target;
        }

        static void SaveAsset(Object asset, string path)
        {
            // 同じメニューを再度実行したとき、既存アセットで作成が止まらないようにする。
            if (AssetDatabase.LoadAssetAtPath<Object>(path) != null)
            {
                AssetDatabase.DeleteAsset(path);
            }
            AssetDatabase.CreateAsset(asset, path);
        }

        static AnimatorController BuildController(string path)
        {
            AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            controller.AddParameter("PrismShot/Enable", AnimatorControllerParameterType.Bool);
            controller.AddParameter("PrismShot/NearDistance", AnimatorControllerParameterType.Float);
            controller.AddParameter("PrismShot/FarDistance", AnimatorControllerParameterType.Float);
            controller.AddParameter("PrismShot/Zoom", AnimatorControllerParameterType.Float);
            controller.AddParameter("PrismShot/DepthPreview", AnimatorControllerParameterType.Bool);
            AnimatorControllerParameter[] parameters = controller.parameters;
            for (int index = 0; index < parameters.Length; index++)
            {
                // 0〜1 の初期位置を、0.3m、10m、視野角 60 度に合わせる。
                if (parameters[index].name == "PrismShot/NearDistance")
                {
                    parameters[index].defaultFloat = 0.031f;
                }
                else if (parameters[index].name == "PrismShot/FarDistance")
                {
                    parameters[index].defaultFloat = 0.310f;
                }
                else if (parameters[index].name == "PrismShot/Zoom")
                {
                    parameters[index].defaultFloat = 0.8f;
                }
            }
            controller.parameters = parameters;
            AnimationClip enableOff = ClipActive("EnableOff", "Rig", false);
            AnimationClip enableOn = ClipActive("EnableOn", "Rig", true);
            AnimationClip previewOff = ClipActive("PreviewOff", "Rig/Preview", false);
            AnimationClip previewOn = ClipActive("PreviewOn", "Rig/Preview", true);
            AnimationClip nearLow = ClipMeters("NearLow", "_NearMeters", 0.15f);
            AnimationClip nearHigh = ClipMeters("NearHigh", "_NearMeters", 5f);
            AnimationClip farLow = ClipMeters("FarLow", "_FarMeters", 1f);
            AnimationClip farHigh = ClipMeters("FarHigh", "_FarMeters", 30f);
            AnimationClip zoomLow = ClipFov("ZoomLow", 20f);
            AnimationClip zoomHigh = ClipFov("ZoomHigh", 70f);
            AnimationClip[] clips =
            {
                enableOff, enableOn, previewOff, previewOn, nearLow, nearHigh, farLow, farHigh, zoomLow, zoomHigh,
            };
            for (int index = 0; index < clips.Length; index++)
            {
                AssetDatabase.AddObjectToAsset(clips[index], controller);
            }
            AnimatorStateMachine machine = controller.layers[0].stateMachine;
            AnimatorState off = machine.AddState("Off");
            AnimatorState on = machine.AddState("On");
            off.motion = enableOff;
            on.motion = enableOn;
            off.writeDefaultValues = false;
            on.writeDefaultValues = false;
            machine.defaultState = off;
            AnimatorStateTransition toOn = off.AddTransition(on);
            toOn.hasExitTime = false;
            toOn.duration = 0f;
            toOn.AddCondition(AnimatorConditionMode.If, 0f, "PrismShot/Enable");
            AnimatorStateTransition toOff = on.AddTransition(off);
            toOff.hasExitTime = false;
            toOff.duration = 0f;
            toOff.AddCondition(AnimatorConditionMode.IfNot, 0f, "PrismShot/Enable");
            AddBlend(controller, "Near", "PrismShot/NearDistance", nearLow, nearHigh);
            AddBlend(controller, "Far", "PrismShot/FarDistance", farLow, farHigh);
            AddBlend(controller, "Zoom", "PrismShot/Zoom", zoomLow, zoomHigh);
            AddBoolLayer(controller, "DepthPreview", "PrismShot/DepthPreview", previewOff, previewOn);
            EditorUtility.SetDirty(controller);
            return controller;
        }

        static AnimationClip ClipActive(string name, string path, bool active)
        {
            AnimationClip clip = new AnimationClip { name = name };
            AnimationCurve curve = new AnimationCurve(new Keyframe(0f, active ? 1f : 0f));
            clip.SetCurve(path, typeof(GameObject), "m_IsActive", curve);
            return clip;
        }

        static AnimationClip ClipMeters(string name, string property, float meters)
        {
            AnimationClip clip = new AnimationClip { name = name };
            AnimationCurve curve = new AnimationCurve(new Keyframe(0f, meters), new Keyframe(1f / 60f, meters));
            // カードの目印と、深度を色にする板の両方を同じ距離範囲にする。
            clip.SetCurve("Rig/Card", typeof(MeshRenderer), "material." + property, curve);
            clip.SetCurve("Rig/DepthCamera/Overlay", typeof(MeshRenderer), "material." + property, curve);
            return clip;
        }

        static AnimationClip ClipFov(string name, float fov)
        {
            AnimationClip clip = new AnimationClip { name = name };
            AnimationCurve curve = new AnimationCurve(new Keyframe(0f, fov), new Keyframe(1f / 60f, fov));
            clip.SetCurve("Rig/ColorCamera", typeof(Camera), "field of view", curve);
            clip.SetCurve("Rig/DepthCamera", typeof(Camera), "field of view", curve);
            return clip;
        }

        static void AddBlend(AnimatorController controller, string layerName, string parameter, Motion low, Motion high)
        {
            BlendTree tree = new BlendTree
            {
                name = layerName,
                blendType = BlendTreeType.Simple1D,
                blendParameter = parameter,
                useAutomaticThresholds = false,
            };
            AssetDatabase.AddObjectToAsset(tree, controller);
            tree.AddChild(low, 0f);
            tree.AddChild(high, 1f);
            AddMotionLayer(controller, layerName, tree);
        }

        static void AddBoolLayer(AnimatorController controller, string layerName, string parameter, Motion off, Motion on)
        {
            controller.AddLayer(layerName);
            AnimatorControllerLayer[] layers = controller.layers;
            int index = layers.Length - 1;
            AnimatorControllerLayer layer = layers[index];
            layer.defaultWeight = 1f;
            AnimatorStateMachine machine = layer.stateMachine;
            AnimatorState offState = machine.AddState("Off");
            AnimatorState onState = machine.AddState("On");
            offState.motion = off;
            onState.motion = on;
            offState.writeDefaultValues = false;
            onState.writeDefaultValues = false;
            machine.defaultState = offState;
            AnimatorStateTransition toOn = offState.AddTransition(onState);
            toOn.hasExitTime = false;
            toOn.duration = 0f;
            toOn.AddCondition(AnimatorConditionMode.If, 0f, parameter);
            AnimatorStateTransition toOff = onState.AddTransition(offState);
            toOff.hasExitTime = false;
            toOff.duration = 0f;
            toOff.AddCondition(AnimatorConditionMode.IfNot, 0f, parameter);
            layers[index] = layer;
            controller.layers = layers;
        }

        static void AddMotionLayer(AnimatorController controller, string layerName, Motion motion)
        {
            controller.AddLayer(layerName);
            AnimatorControllerLayer[] layers = controller.layers;
            int index = layers.Length - 1;
            AnimatorControllerLayer layer = layers[index];
            // 追加レイヤーは初期ウェイトが 0 なので、常に混ぜる。
            layer.defaultWeight = 1f;
            AnimatorState state = layer.stateMachine.AddState(layerName);
            state.motion = motion;
            state.writeDefaultValues = false;
            layers[index] = layer;
            controller.layers = layers;
        }

        static VRCExpressionsMenu BuildMenu(string path)
        {
            VRCExpressionsMenu menu = ScriptableObject.CreateInstance<VRCExpressionsMenu>();
            menu.controls = new List<VRCExpressionsMenu.Control>
            {
                Toggle("出す", "PrismShot/Enable"),
                Radial("近い距離", "PrismShot/NearDistance"),
                Radial("遠い距離", "PrismShot/FarDistance"),
                Radial("ズーム", "PrismShot/Zoom"),
                Toggle("深度プレビュー", "PrismShot/DepthPreview"),
            };
            SaveAsset(menu, path);
            return menu;
        }

        static VRCExpressionsMenu.Control Toggle(string label, string parameter)
        {
            return new VRCExpressionsMenu.Control
            {
                name = label,
                type = VRCExpressionsMenu.Control.ControlType.Toggle,
                parameter = new VRCExpressionsMenu.Control.Parameter { name = parameter },
                value = 1f,
            };
        }

        static VRCExpressionsMenu.Control Radial(string label, string parameter)
        {
            VRCExpressionsMenu.Control control = new VRCExpressionsMenu.Control
            {
                name = label,
                type = VRCExpressionsMenu.Control.ControlType.RadialPuppet,
            };
            if (control.subParameters == null || control.subParameters.Length == 0)
            {
                control.subParameters = new VRCExpressionsMenu.Control.Parameter[2];
            }
            control.subParameters[0] = new VRCExpressionsMenu.Control.Parameter { name = parameter };
            return control;
        }

        static GameObject BuildHierarchy(
            RenderTexture colorRt,
            RenderTexture depthRt,
            Material cardMat,
            Material depthMat,
            Material previewMat,
            Material bodyMat,
            AnimatorController controller,
            VRCExpressionsMenu menu)
        {
            GameObject root = new GameObject("PrismShot");
            root.AddComponent<PrismShotRoot>();
            GameObject rig = new GameObject("Rig");
            rig.transform.SetParent(root.transform, false);
            // 出していない間はカメラを止める。Animator がオンのときだけ有効になる。
            rig.SetActive(false);
            Camera colorCam = CreateCamera(rig.transform, "ColorCamera", colorRt, false);
            Camera depthCam = CreateCamera(rig.transform, "DepthCamera", depthRt, true);
            GameObject overlay = CreateQuad(depthCam.transform, "Overlay", 2, depthMat);
            overlay.transform.localPosition = new Vector3(0f, 0f, 0.5f);
            overlay.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            overlay.transform.localScale = new Vector3(5f, 5f, 1f);
            GameObject card = CreateQuad(rig.transform, "Card", 4, cardMat);
            card.transform.localPosition = new Vector3(0f, 0.05f, -0.12f);
            card.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            card.transform.localScale = new Vector3(0.16f, 0.08f, 1f);
            GameObject preview = CreateQuad(rig.transform, "Preview", 4, previewMat);
            preview.transform.localPosition = new Vector3(0.1f, 0.05f, -0.12f);
            preview.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            preview.transform.localScale = new Vector3(0.06f, 0.06f, 1f);
            preview.SetActive(false);
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "Body";
            Object.DestroyImmediate(body.GetComponent<Collider>());
            body.layer = 4;
            body.transform.SetParent(rig.transform, false);
            body.transform.localScale = new Vector3(0.08f, 0.05f, 0.04f);
            body.GetComponent<MeshRenderer>().sharedMaterial = bodyMat;
            Animator animator = root.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            ModularAvatarMergeAnimator merge = root.AddComponent<ModularAvatarMergeAnimator>();
            merge.animator = controller;
            merge.layerType = VRCAvatarDescriptor.AnimLayerType.FX;
            merge.pathMode = MergeAnimatorPathMode.Relative;
            merge.deleteAttachedAnimator = true;
            merge.matchAvatarWriteDefaults = true;
            merge.mergeAnimatorMode = MergeAnimatorMode.Append;
            ModularAvatarMenuInstaller installer = root.AddComponent<ModularAvatarMenuInstaller>();
            installer.menuToAppend = menu;
            installer.installTargetMenu = VRCAvatarDescriptor.AnimLayerType.FX;
            ModularAvatarParameters parameters = root.AddComponent<ModularAvatarParameters>();
            // NotSynced はメニューへ登録されない。種類は Bool/Float にし、同期だけ切る。
            parameters.parameters = new List<ParameterConfig>
            {
                Param("PrismShot/Enable", ParameterSyncType.Bool, 0f),
                Param("PrismShot/NearDistance", ParameterSyncType.Float, 0.031f),
                Param("PrismShot/FarDistance", ParameterSyncType.Float, 0.310f),
                Param("PrismShot/Zoom", ParameterSyncType.Float, 0.8f),
                Param("PrismShot/DepthPreview", ParameterSyncType.Bool, 0f),
            };
            return root;
        }

        static ParameterConfig Param(string name, ParameterSyncType type, float value)
        {
            return new ParameterConfig
            {
                nameOrPrefix = name,
                syncType = type,
                localOnly = true,
                saved = false,
                defaultValue = value,
                hasExplicitDefaultValue = true,
            };
        }

        static Camera CreateCamera(Transform parent, string name, RenderTexture target, bool depth)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            Camera camera = go.AddComponent<Camera>();
            camera.nearClipPlane = 0.05f;
            camera.farClipPlane = 30f;
            camera.fieldOfView = 60f;
            camera.allowHDR = false;
            camera.allowMSAA = false;
            camera.targetTexture = target;
            int hidden = 1 << 4;
            int overlay = 1 << 2;
            if (depth)
            {
                // 世界と深度用の板は映し、持ち手とカードは映さない。
                camera.cullingMask = ~hidden;
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = Color.black;
                camera.depthTextureMode = DepthTextureMode.Depth;
                camera.depth = 1f;
            }
            else
            {
                camera.cullingMask = ~(hidden | overlay);
                camera.clearFlags = CameraClearFlags.Skybox;
                camera.depth = 0f;
            }
            return camera;
        }

        static GameObject CreateQuad(Transform parent, string name, int layer, Material material)
        {
            GameObject quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad.name = name;
            Object.DestroyImmediate(quad.GetComponent<Collider>());
            quad.layer = layer;
            quad.transform.SetParent(parent, false);
            quad.GetComponent<MeshRenderer>().sharedMaterial = material;
            return quad;
        }

        static void EnsureFolder(string folder)
        {
            if (AssetDatabase.IsValidFolder(folder))
            {
                return;
            }
            string parent = Path.GetDirectoryName(folder).Replace("\\", "/");
            if (parent != "Assets" && !AssetDatabase.IsValidFolder(parent))
            {
                EnsureFolder(parent);
            }
            AssetDatabase.CreateFolder(parent, Path.GetFileName(folder));
        }
    }
}
