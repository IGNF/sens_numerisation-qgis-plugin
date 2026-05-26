from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsRendererCategory, QgsCategorizedSymbolRenderer,QgsSimpleMarkerSymbolLayer,
                       QgsSymbol, QgsWkbTypes, QgsMarkerLineSymbolLayer,QgsSingleSymbolRenderer,
                       QgsRuleBasedRenderer, QgsProject)

from .mapping_version import *

class SensNumerisation:
    def __init__(self, iface):
        self.layer = None
        self.iface = iface
        self.is_affiche_sens_num = False

    def initGui(self):
        pass

    def unload(self):
        pass

    def init_symbole(self):
        # Créer le triangle comme SimpleMarkerLayer
        triangle_layer = QgsSimpleMarkerSymbolLayer()
        triangle_layer.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
        triangle_layer.setColor(QColor(0, 0, 255))
        triangle_layer.setSize(2)
        triangle_layer.setAngle(90)

        # Créer un QgsSymbol pour le MarkerLine
        triangle_symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
        triangle_symbol.deleteSymbolLayer(0)  # supprime le SimpleMarker par défaut
        triangle_symbol.appendSymbolLayer(triangle_layer)

        ml = QgsMarkerLineSymbolLayer()
        ml.setSubSymbol(triangle_symbol)  # ⚡ ici on passe un QgsSymbol
        ml.setPlacement(QgsMarkerLineSymbolLayer.Interval)
        ml.setInterval(20)
        ml.setOffset(0)
        return ml

    def add_symb_sens_num(self,layer):
        renderer = layer.renderer()

        if renderer.type() == "singleSymbol":
            ml = self.init_symbole()
            # Ajouter la MarkerLine au symbole existant
            sym = renderer.symbol().clone()
            sym.appendSymbolLayer(ml)

            layer.setRenderer(QgsSingleSymbolRenderer(sym))
            layer.setCustomProperty("extra_triangle_single",sym.symbolLayerCount() - 1)

        elif renderer.type() == "RuleRenderer":
            root = renderer.rootRule().clone()
            rules_to_process = [root]
            while rules_to_process:
                rule = rules_to_process.pop()
                sym = rule.symbol()
                if sym:
                    sym = sym.clone()
                    ml = self.init_symbole()
                    sym.appendSymbolLayer(ml)
                    rule.setSymbol(sym)
                rules_to_process.extend(rule.children())
            layer.setRenderer(QgsRuleBasedRenderer(root))

        elif renderer.type() == "categorizedSymbol":
            new_categories = []
            for cat in renderer.categories():
                sym = cat.symbol().clone()  # cloner le symbole existant
                ml = self.init_symbole()
                # Ajouter la MarkerLine au symbole existant
                sym.appendSymbolLayer(ml)
                # Stocker un identifiant pour suppression future
                layer.setCustomProperty(f"categorie_{cat.value()}", sym.symbolLayerCount() - 1)
                # Nouvelle catégorie
                new_cat = QgsRendererCategory(cat.value(), sym, cat.label())
                new_categories.append(new_cat)

            # Appliquer le nouveau renderer
            new_renderer = QgsCategorizedSymbolRenderer(renderer.classAttribute(), new_categories)
            layer.setRenderer(new_renderer)
        layer.triggerRepaint()


    def suppr_symb_sens_num(self,layer):
        renderer = layer.renderer()
        if renderer.type() == "singleSymbol":
            sym = renderer.symbol().clone()
            idx = layer.customProperty("extra_triangle_single", None)
            if idx is not None:
                idx = int(idx)
                if 0 <= idx < sym.symbolLayerCount():
                    sym.deleteSymbolLayer(idx)
                layer.removeCustomProperty("extra_triangle_single")
            layer.setRenderer(QgsSingleSymbolRenderer(sym))

        elif renderer.type() == "RuleRenderer":
            root = renderer.rootRule().clone()
            rules_to_process = [root]
            while rules_to_process:
                rule = rules_to_process.pop()
                rule_sym = rule.symbol()
                if rule_sym:
                    sym = rule_sym.clone()
                    # Supprimer uniquement le dernier MarkerLine (le triangle ajouté)
                    for i in reversed(range(sym.symbolLayerCount())):
                        sl = sym.symbolLayer(i)
                        if isinstance(sl, QgsMarkerLineSymbolLayer):
                            sym.deleteSymbolLayer(i)
                            break  # on supprime seulement le dernier
                    rule.setSymbol(sym)
                rules_to_process.extend(rule.children())
            layer.setRenderer(QgsRuleBasedRenderer(root))

        elif renderer.type() == "categorizedSymbol":
            new_categories = []
            for cat in renderer.categories():
                sym = cat.symbol().clone()  # clone pour ne pas modifier l'original
                # Supprimer uniquement le dernier MarkerLine ajouté
                for i in reversed(range(sym.symbolLayerCount())):
                    sl = sym.symbolLayer(i)
                    if isinstance(sl, QgsMarkerLineSymbolLayer):
                        sym.deleteSymbolLayer(i)
                        break  # on supprime seulement le dernier ajouté
                # Recréer la catégorie avec le symbole modifié
                new_cat = QgsRendererCategory(cat.value(), sym, cat.label())
                new_categories.append(new_cat)
            # Recréer le renderer catégorisé
            new_renderer = QgsCategorizedSymbolRenderer(renderer.classAttribute(), new_categories)
            layer.setRenderer(new_renderer)
        layer.triggerRepaint()

    def run(self):
        projet = QgsProject.instance()
        if len(projet.mapLayers()) <= 0:
            QMessageBox.warning(self.iface.mainWindow(), "Attention", "veuillez charger un projet", QMessageBox.Ok)
            return
        self.layer = self.iface.activeLayer()
        if not self.layer:
            return
        print(self.is_affiche_sens_num)
        if self.is_affiche_sens_num:
            self.suppr_symb_sens_num(self.layer)
            self.is_affiche_sens_num = False
        else:
            self.add_symb_sens_num(self.layer)
            self.is_affiche_sens_num = True
        self.layer.triggerRepaint()
