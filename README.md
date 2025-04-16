# Lab-Film-Recommender

Detta är en laboration i maskininlärning där ett enklare system för att rekommendera filmer har utvecklats.

Data för detta är hämtad från [movielens](https://grouplens.org/datasets/movielens/), där ml-latest.zip laddades ner under sektionen "recommended for education and development".

För att köra denna applikation och använda rekommendationssystemet, behöver denna data laddas ner och läggas under mappen _data_.

Data-filerna som behövs för applikationen är _movies.csv_, _ratings.csv_ och _tags.csv_.

Programmet körs som en dash-applikation lokalt och startas genom att köra _main.py_.

Vid utvecklingen av rekommendationsmotorn uppstod en del frågeställningar kring vad det innebär att rekommendera en film.
Ska systemet försöka hitta filmer som är objektivt lika den valda filmen, eller ska det föreslå filmer som har liknande trender i betygsättning?
Om målet är att hitta liknande filmer borde större vikt läggas vid genrer och tags.
Samtidigt finns det då en risk att de liknande filmerna som rekommenderas har fått dåliga betyg och ändå inte passar för användaren.

För denna rekommendationsmotor är det collaborative filtering som väger mest, där betygsbaserad likhet används, och alltså mönster i hur användare har satt betyg. Om till exempel en stor andel användare som gav _Forrest Gump (1994)_ 5 i betyg även gav _Jumanji (1995)_ 5 i betyg, anses dessa filmer vara relaterade i smak, även om de har helt olika henrer.

Utöver betygsdata, används även tags som användare skrivit in kombinerat med genrer för varje film. Här används TF-IDF vektorisering för att hitta andra likheter mellan filmerna. Detta kan då ge en högre likhet mellan filmer av exakt samma genrer, eller om användare skrivit in skådespelares namn i tags på filmerna.

För att skapa en bättre rekommendation kombineras dessa modeller. Likheterna viktas samman där betygsbaserad likhet står för 70% och innehållsbaserad likhet för 30% av den totala rekommendationsmatchningen. Detta gör att rekommendationerna främst styrs av användarnas betygsmönster, men med stöd från genrer och tags.
Slutresultatet är en rekommendationsmatchning för varje film i procent, då från 0 till 100, som visas för användaren. En hög procent indikerar att filmen är starkt rekommenderad baserat på den valda filmen.

Något som upptäcktes dock är att en del filmer inte får höga procent i rekommendationsmatchning alls.
Exakt vad detta betyder är svårt att säga, förutom att ingen bra koppling hittades till andra filmer både när det kommer till betygmönster och tags/genrer.

En annan upptäckt var att filmer med uppföljare ofta resulterar i hög rekommendation av uppföljare.
Några exempel på detta är Toy Story, Star Wars, Hunger Games, Spider-Man.
Detta känns rimligt. Om en användare såg Toy Story 1 och gillade denna, kommer användaren troligtvis kolla på 2:an.
En hög rekommendationsmatch betyder då att många användare som gillade första filmen även gillade andra filmen.
När det kommer till likhet i tags och genre borde detta också resultera i hög likhet mellan uppföljare.

Då det finns en väldigt stor mängd filmer, tags och framförallt ratings har data valt att begränsas för detta rekommendationssystem.
För att minska antalet gjordes beslutet att filmer som inkluderas måste ha minst 1000 betygsättningar, och dessutom används bara betyg från användare som betygsatt minst 1000 filmer.
Detta har gjorts för prestanda, men även för att endast ha med relevanta betygsättningar.
En användare som endast betygsatt fem filmer kan vara svår att dra slutsatser utifrån.

