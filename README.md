# Lab-Film-Recommender

Detta är en laboration i maskininlärning där ett enklare system för att rekommendera filmer har utvecklats.

Data för detta projekt är hämtad från [movielens](https://grouplens.org/datasets/movielens/), där ml-latest.zip laddades ner under sektionen "recommended for education and development".

För att köra denna applikation och använda rekommendationssystemet, behöver denna data laddas ner och läggas under mappen _data_.

Data-filerna som behövs för applikationen är _movies.csv_, _ratings.csv_ och _tags.csv_.

Programmet körs som en dash-applikation lokalt och startas genom att köra _main.py_.

Vid utvecklingen av rekommendationsmotorn uppstod en del frågeställningar kring vad det innebär att rekommendera en film.
Ska systemet försöka hitta filmer som är objektivt lika den valda filmen, eller ska det föreslå filmer som har liknande trender i betygsättning?
Om målet är att hitta liknande filmer borde större vikt läggas vid genrer och tags.
Samtidigt finns det då en risk att de liknande filmerna som rekommenderas har fått dåliga betyg och ändå inte passar för användaren.

För rekommendationsmotorn i detta system är det framförallt collaborative filtering som gäller, där betygsbaserad likhet används, och alltså mönster i hur användare har satt betyg. Om till exempel en stor andel användare som gav _Forrest Gump (1994)_ 5 i betyg även gav _Jumanji (1995)_ 5 i betyg, anses dessa filmer vara relaterade i smak, även om de har helt olika genrer. För detta skapas en pivot-tabell med alla movieId som index, alla userId som kolumner, och betygen som värden. Om en användare inte betygsatt en film fylls detta med 0. Den matris som skapas skaleras sedan med standardisering, för att se till att likheten beräknas baserat på betygsmönster och inte de absoluta värdena. Vissa användare kanske alltid sätter mellan 3 och 5 i betyg, medan några bara sätter mellan 2 och 4. Genom att skala betygen jämnas dessa skillnader ut och modellen fokuserar på hur varje användare avviker från sin egen genomsnittliga betygsnivå.

Utöver betygsdata, används även tags som användare skrivit in kombinerat med genrer för varje film. Här används TF-IDF vektorisering för att identifiera filmer som delar viktiga nyckelord. Detta kan då ge en högre likhet mellan filmer med exakt samma genrer, eller om filmer till exempel har samma skådespelare, och användare har skrivit in skådespelarens namn i tags på filmerna. För både betygsmönster-matrisen och TF-IDF vektoriseringen används cosinus-likhet för att få fram likheterna mellan alla filmer.

För att skapa en bättre rekommendation kombineras dessa modeller. Likheterna viktas samman där betygsbaserad likhet står för 70% och innehållsbaserad likhet för 30% av den totala rekommendationsmatchningen. Detta gör att rekommendationerna främst styrs av användarnas betygsmönster, men med stöd från genrer och tags.
Slutresultatet är en rekommendationsmatchning för varje film i procent, då från 0 till 100, som visas för användaren. En hög procent indikerar att filmen är starkt rekommenderad baserat på den valda filmen.

Något som upptäcktes när rekommendationssystemet användes var att en del filmer inte får höga procent i rekommendationsmatchning med någon film alls.
Exakt vad detta betyder är svårt att säga, förutom att ingen bra koppling hittades till andra filmer varken i betygsmönster eller tags/genrer.

En annan upptäckt var att filmer med uppföljare ofta resulterar i hög rekommendationsmatch för sina andra delar, vilket känns rimligt.
Några exempel på detta är Toy Story, Star Wars, Hunger Games och Spider-Man.
Om en användare såg Toy Story 1 och gillade denna, kommer användaren troligtvis kolla på Toy Story 2.
En hög rekommendationsmatch betyder då att många användare som gillade första filmen även gillade andra filmen.
När det kommer till likhet i tags/genre borde detta också resultera i ett högt värde eftersom uppföljare ofta delar liknande innehåll som genrer, karaktärer, miljöer med mera.

Då det finns en väldigt stor mängd filmer, tags och framförallt ratings har data valt att begränsas för detta rekommendationssystem.
För att minska antalet gjordes beslutet att filmer som inkluderas måste ha minst 1000 betygsättningar, och dessutom används bara betyg från användare som betygsatt minst 1000 filmer.
Detta val gjordes dels av prestandaskäl, men också för att endast ha med relevanta betygsättningar. En användare som endast betygsatt ett fåtal filmer kan vara svår att dra slutsatser utifrån.

Att utvärdera hur bra detta rekommendationssystem fungerar är svårt, eftersom det inte finns något facit över vilka filmer som borde rekommenderats för varje film. För att kunna få någon statistik på det hade det krävts att ta hänsyn till olika användare, och förutspå vilka betyg de hade satt på filmerna, för att sedan jämföra med vad de faktiskt satte för betyg. För en sådan utvärdering behöver datan hanteras på andra sätt, och andra modeller och metoder borde utforskas.

I detta projekt har utvärdering främst skett genom att själv undersöka vilka rekommendationer som genereras för filmer jag känner till och uppskattar, och för de flesta av dessa filmer anser jag att rekommendationerna är relevanta och rimliga.
