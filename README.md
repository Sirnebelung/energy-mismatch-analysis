# Analyse af energimismatch og elpriser i Danmark

Analyse af mismatch mellem energiproduktion og forbrug i Danmark samt sammenhængen med elpriser og vedvarende energi.  
Data er behandlet i Python og efterfølgende visualiseret i Power BI.

## Data
- Energinet API  
- Elspotprices  
- ProductionConsumption  

## Metode
- Data ingestion og behandling i Python  
- Merge på HourUTC + PriceArea  
- Feature engineering:
  - mismatch (produktion - forbrug)  
  - renewable_share (andel vedvarende energi)  
- Visualisering og analyse i Power BI  

## Insights

### Insight 1 – Mismatch vs pris
Der er en tydelig negativ sammenhæng mellem mismatch og elpris, hvilket indikerer, at overskud af strøm presser priserne ned.

### Insight 2 – Renewable vs pris
Analysen viser, at vedvarende energikilder har en stærkere påvirkning på elpriser end det samlede mismatch mellem produktion og forbrug. Dette understreger betydningen af energikildens sammensætning i prisdannelsen.

### Insight 3 – Geografi
Vestdanmark (DK1) har systematisk overskud, mens Østdanmark (DK2) har underskud, hvilket indikerer behov for energiflow eller import.

### Insight 4 – Mismatch over tid
Elsystemet er dynamisk med betydelige udsving i balancen mellem produktion og forbrug. Dette understreger behovet for fleksibilitet i energisystemet, herunder lagring og styring af efterspørgsel.

### Insight 5 – Grøn energi vs pris
Visualiseringen viser en tydelig negativ sammenhæng mellem andelen af vedvarende energi og elpriser, hvilket indikerer, at høj produktion fra vind og sol presser priserne ned. Samtidig fremstår Østdanmark (DK2) med større prisudsving, hvilket tyder på en højere afhængighed af import og eksterne markedsforhold.

## Visualiseringer

### Elbalance over tid
![Elbalance over tid](images/mismatch_chart.png)

### Elpris vs andel vedvarende energi
![Elpris vs vedvarende energi](images/renewable_price_scatter.png)