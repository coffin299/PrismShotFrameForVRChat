// SPDX-License-Identifier: Apache-2.0
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace PrismShotFrame.Editor
{
    /// <summary>
    /// 額縁3種、画像名の読み取り、サンプルシーンを作る。
    /// </summary>
    public static class PrismShotFrameBuilder
    {
        const string Folder = "Assets/PrismShotFrame/Generated";
        static readonly Regex QuiltName = new Regex(
            @"qs(\d+)x(\d+)a([0-9]*\.?[0-9]+)",
            RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);

        [MenuItem("PrismShot/Build Frame Prefabs")]
        public static void BuildPrefabs()
        {
            BuildCore(true);
        }

        static bool BuildCore(bool notify)
        {
            Shader picture = Shader.Find("PrismShotFrame/RGBD");
            Shader wood = Shader.Find("PrismShotFrame/UnlitColor");
            if (picture == null || wood == null)
            {
                EditorUtility.DisplayDialog("PrismShotFrame", "額縁のシェーダーが見つかりません。", "OK");
                return false;
            }
            EnsureFolder(Folder);
            Material pictureMat = new Material(picture);
            pictureMat.SetFloat("_Strength", 0.03f);
            pictureMat.SetFloat("_Focus", 0.5f);
            SaveAsset(pictureMat, Folder + "/PictureRGBD.mat");
            Material frameMat = new Material(wood);
            frameMat.SetColor("_Color", new Color(0.22f, 0.16f, 0.12f));
            SaveAsset(frameMat, Folder + "/FrameWood.mat");
            Mesh cube = BuiltinMesh(PrimitiveType.Cube);
            CreateFlat(pictureMat);
            CreateFramed("PrismShotFrame_Border", pictureMat, frameMat, cube, 0.03f);
            CreateFramed("PrismShotFrame_Thick", pictureMat, frameMat, cube, 0.08f);
            AssetDatabase.SaveAssets();
            if (notify)
            {
                EditorUtility.DisplayDialog("PrismShotFrame", "額縁プレハブを3つ作りました。Quest では RGB-D のまま使ってください。", "OK");
            }
            return true;
        }

        [MenuItem("PrismShot/Read Picture Name On Selection")]
        public static void ReadSelection()
        {
            GameObject selected = Selection.activeGameObject;
            if (selected == null)
            {
                EditorUtility.DisplayDialog("PrismShotFrame", "額縁の絵のオブジェクトを選んでください。", "OK");
                return;
            }
            Renderer renderer = selected.GetComponent<Renderer>();
            if (renderer == null || renderer.sharedMaterial == null)
            {
                return;
            }
            Material material = renderer.sharedMaterial;
            Texture texture = material.GetTexture("_MainTex");
            if (texture == null)
            {
                EditorUtility.DisplayDialog("PrismShotFrame", "マテリアルに画像がありません。", "OK");
                return;
            }
            ApplyTexture(material, texture);
            EditorUtility.SetDirty(material);
        }

        [MenuItem("PrismShot/Create Sample Scene")]
        public static void CreateSample()
        {
            if (!EditorUtility.DisplayDialog("PrismShotFrame", "新しいシーンに額縁を3つ置きます。今のシーンは保存してください。", "作成", "中止"))
            {
                return;
            }
            if (!BuildCore(false))
            {
                return;
            }
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            Place("PrismShotFrame_Flat", new Vector3(-2f, 1.5f, 2f));
            Place("PrismShotFrame_Border", new Vector3(0f, 1.5f, 2f));
            Place("PrismShotFrame_Thick", new Vector3(2f, 1.5f, 2f));
            EnsureFolder(Folder);
            EditorSceneManager.SaveScene(scene, Folder + "/Sample.unity");
        }

        static void ApplyTexture(Material material, Texture texture)
        {
            string assetPath = AssetDatabase.GetAssetPath(texture);
            Match match = QuiltName.Match(texture.name);
            bool quilt = match.Success;
            Shader shader = Shader.Find(quilt ? "PrismShotFrame/Quilt" : "PrismShotFrame/RGBD");
            if (shader == null)
            {
                return;
            }
            material.shader = shader;
            material.SetTexture("_MainTex", texture);
            if (quilt)
            {
                int columns = int.Parse(match.Groups[1].Value);
                int rows = int.Parse(match.Groups[2].Value);
                material.SetFloat("_Columns", columns);
                material.SetFloat("_Rows", rows);
                material.SetFloat("_ViewCount", columns * rows);
                material.SetFloat("_MaxAngle", 0.45f);
            }
            else
            {
                material.SetFloat("_Strength", 0.03f);
                material.SetFloat("_Focus", 0.5f);
            }
            TextureImporter importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            if (importer == null)
            {
                return;
            }
            // RGB-D は圧縮とミップマップで深度のバイトが崩れる。
            importer.textureCompression = quilt
                ? TextureImporterCompression.CompressedHQ
                : TextureImporterCompression.Uncompressed;
            importer.mipmapEnabled = quilt;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.SaveAndReimport();
        }

        static void CreateFlat(Material pictureMat)
        {
            GameObject root = new GameObject("PrismShotFrame_Flat");
            GameObject picture = CreatePicture(root.transform, pictureMat, "PrismShotFrame_Flat");
            picture.transform.localScale = new Vector3(1.6f, 0.9f, 1f);
            AddSlideshow(root, picture.GetComponent<Renderer>());
            PrefabUtility.SaveAsPrefabAsset(root, Folder + "/PrismShotFrame_Flat.prefab");
            Object.DestroyImmediate(root);
        }

        static void CreateFramed(string name, Material pictureMat, Material frameMat, Mesh cube, float depth)
        {
            GameObject root = new GameObject(name);
            GameObject frame = new GameObject("Frame");
            frame.transform.SetParent(root.transform, false);
            MeshFilter filter = frame.AddComponent<MeshFilter>();
            filter.sharedMesh = BuildFrameMesh(cube, depth);
            MeshRenderer renderer = frame.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = frameMat;
            GameObject picture = CreatePicture(root.transform, pictureMat, name);
            picture.transform.localPosition = new Vector3(0f, 0f, depth * 0.5f + 0.01f);
            picture.transform.localScale = new Vector3(1.4f, 0.78f, 1f);
            AddSlideshow(root, picture.GetComponent<Renderer>());
            string meshPath = Folder + "/" + name + ".asset";
            SaveAsset(filter.sharedMesh, meshPath);
            PrefabUtility.SaveAsPrefabAsset(root, Folder + "/" + name + ".prefab");
            Object.DestroyImmediate(root);
        }

        static Mesh BuildFrameMesh(Mesh cube, float depth)
        {
            List<CombineInstance> parts = new List<CombineInstance>();
            AddBox(parts, cube, new Vector3(0f, 0f, -depth * 0.5f), new Vector3(1.7f, 1.0f, depth));
            AddBox(parts, cube, new Vector3(0f, 0.46f, 0f), new Vector3(1.7f, 0.08f, depth));
            AddBox(parts, cube, new Vector3(0f, -0.46f, 0f), new Vector3(1.7f, 0.08f, depth));
            AddBox(parts, cube, new Vector3(-0.81f, 0f, 0f), new Vector3(0.08f, 1.0f, depth));
            AddBox(parts, cube, new Vector3(0.81f, 0f, 0f), new Vector3(0.08f, 1.0f, depth));
            Mesh mesh = new Mesh { name = "Frame" };
            mesh.CombineMeshes(parts.ToArray(), true, true);
            return mesh;
        }

        static void AddBox(List<CombineInstance> parts, Mesh cube, Vector3 position, Vector3 scale)
        {
            parts.Add(new CombineInstance
            {
                mesh = cube,
                transform = Matrix4x4.TRS(position, Quaternion.identity, scale),
            });
        }

        static GameObject CreatePicture(Transform parent, Material material, string assetName)
        {
            GameObject picture = GameObject.CreatePrimitive(PrimitiveType.Quad);
            picture.name = "Picture";
            Object.DestroyImmediate(picture.GetComponent<Collider>());
            picture.transform.SetParent(parent, false);
            Material copy = new Material(material);
            SaveAsset(copy, Folder + "/" + assetName + "_Picture.mat");
            picture.GetComponent<MeshRenderer>().sharedMaterial = copy;
            return picture;
        }

        static void AddSlideshow(GameObject root, Renderer picture)
        {
            PrismShotSlideshow slideshow = root.AddComponent<PrismShotSlideshow>();
            slideshow.target = picture;
            slideshow.intervalSeconds = 5f;
        }

        static void Place(string name, Vector3 position)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Folder + "/" + name + ".prefab");
            if (prefab == null)
            {
                return;
            }
            GameObject instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            instance.transform.position = position;
        }

        static Mesh BuiltinMesh(PrimitiveType type)
        {
            GameObject temp = GameObject.CreatePrimitive(type);
            Mesh mesh = temp.GetComponent<MeshFilter>().sharedMesh;
            Object.DestroyImmediate(temp);
            return mesh;
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
