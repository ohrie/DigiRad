# DigiRad

Geplant ist ein QGIS-Plugin zur Radnetzentwicklung, genauer in der Zielnetzplanung.

Diese Repository ist für die technisch orientierten Arbeitspakete gedacht. 

# Stand der Dinge
Projektende ist Ende 2025
Rückkopplung mit PK im Sommer 2025

## November 2024
Befragungen stellen nur Anforderungen an das Plugin dar.

### Wofür soll es da sein und was soll das können?
- POIs müssen im Zielnetz verbunden sein -> Auslesen von POIs aus OSM und Ergänzung
- POIs sind z.B. Schulen, Wohnstandorte, usw.
- POIs sollen auch verschiebbar sein -> POIs können auswählbar sein
- Manipulation des POIs in der Netzhierarchiestufe, z.B. Anknüpfungspunkte in das übergeordnete Netz, ähnlich wie bei VISUM mit Kordonanknüpfungselementen
- Anreicherung mit ImmoScout-Daten?
- Verarbeitung der POIs - Clustern? Insbesondere bei Wohnstandorten.
- Halbwegs sinnvolles Netz von POIs
- Ergänzung der POI-Raster zu einem Luftlinienzielnetz
- Umlegung des Luftlinienzielnetzes auf das existierende Straßennetz
- Was für ein Netz wird als Grundlage genommen?
- Welche Umlegung? Kürzeste Reisezeit? Auf Grundlage der Verkehrsmengen aus dem RiDE-Portal? Daraus ein Differenznetz?
- Fokus auf Erkennung der POIs
- Welche Sekundärdaten kann man mit einbeziehen?
- Was soll es denn enthalten? Plotvorlage mit QGIS-Atlanten oder Shapefile?
- Sollte das Shapefile interoperabel mit dem Portal sein?

### Anforderungsworkshops & Tiefeninterviews
- Wie stellen sich die Akteure die Useability vor?
- Welche QGIS-Version nutzen sie?
- Wird GIS überhaupt genutzt?