import json
import urllib.request


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=30))


pw = get("https://www.piwheels.org/project/opencv-python-headless/json/")
hits = [(v, f) for v, r in pw["releases"].items() for f in r.get("files", {}) if "cp37" in f and "armv7l" in f and v.startswith("4.")]
print("opencv-headless 4.x cp37 armv7l on piwheels:", sorted(hits)[-4:])
for pkg in ("tflite-runtime", "onnxruntime", "ncnn"):
    try:
        pp = get("https://pypi.org/pypi/%s/json" % pkg)
        h = [(v, f["filename"]) for v, fs in pp["releases"].items() for f in fs if "cp37" in f["filename"] and "armv7l" in f["filename"]]
        print(pkg, "pypi cp37 armv7l:", h[-3:])
    except Exception as e:
        print(pkg, e)
