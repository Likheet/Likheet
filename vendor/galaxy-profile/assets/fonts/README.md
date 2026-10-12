# Font sources

The generator draws text as outlines, so the SVGs look the same in every
browser and never depend on a font being installed or downloadable. These are
the sources those outlines are built from. `make fonts` reads them and writes
`generator/fonts/*.json`; generating SVGs only reads the JSON.

| File | What it is | Licence |
|---|---|---|
| `Spectral-{Light,Regular,Medium,Italic}.ttf` | [Spectral](https://github.com/productiontype/Spectral), unmodified, from the Google Fonts repository | `OFL-Spectral.txt` |
| `NotoSerif-Italic-greek.ttf` | [Noto Serif](https://github.com/notofonts/latin-greek-cyrillic) Italic, instantiated at weight 400 and subset to Greek lowercase (U+03B1–03C9) | `OFL-NotoSerif.txt` |

Spectral has no Greek lowercase. The featured-projects plate labels its stars
α, β, γ, and those letters come from the Noto Serif subset.

The subset was produced with fontTools:

```python
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.subset import Subsetter, Options

font = instantiateVariableFont(TTFont("NotoSerif-Italic[wdth,wght].ttf"), {"wght": 400, "wdth": 100})
options = Options()
options.layout_features = []
subsetter = Subsetter(options)
subsetter.populate(unicodes=range(0x3B1, 0x3CA))
subsetter.subset(font)
font.save("NotoSerif-Italic-greek.ttf")
```
