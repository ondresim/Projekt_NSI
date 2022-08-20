<div align="center">

# Systém Indoor navigace pomocí Wi-Fi

  Závěrečný projekt předmětu NSI
  
  Šimon Ondřej
  
  17.8. 2022
  
<div align="left">
  
## Cíle
Cílem projektu je vytvoření systému vnitřní navigace za pomoci vývojové desky ESP8266. Deska bude mít za úkol skenovat WiFi access pointy (AP) a z nich získat hodnotu Received Signal Strength Indicator (RSSI). Tato data budou následně ukládána a pomocí nich natrénovány klasifikátory strojového učení.
  
## Rozbor řešení
Projekt se skládá z následujících dílčích částí:
- Sbírání a přenos dat
- Ukládání dat a práce s daty
- Trénování modelů
- Predikce v reálném čase
  
### 1. Sbírání a přenos dat (ESP8266_MQTT.ino):
  
Vývojová deska ESP8266 se nejprve připojí k předem určené Wi-Fi síti pomocí knihovny ESP8266WiFi [1]. Dále začne skenovat SSID a RSSI z AP, které jsou v blízkosti a ukládat data ve formátu python dictionary. 
<br />
<br />
V lokální síti jsou zařízení jedno pro druhé lehce přístupné a mohou spolu bez problémů komunikovat. Ve veřejné síti je však situace horší. Je nutné se nějakým způsobem vypořádat s Network address translation (NAT). NAT je technika, která zajišťuje mapování privátních IP adres na veřejné [2]. Kvůli tomu se nelze snadno z veřejné sítě připojit na určité zařízení v lokální síti.

Možnosti řešení tohoto problému jsou:
  - Port forwarding manuálně na routeru [3]
  -	Dynamický port forwarding pomocí UPnP protokolů [4]
  -	Metoda hole punching [5]
  - Application Layer Gateway (ALG)
  
Alternativním způsobem, jak tento problém obejít, je použít prostředníka ke komunikaci, ke kterému se obě koncová zařízení připojí a komunikují skrz něj. Takovýmto prostředníkem může být například MQTT broker [6].
  
Právě komunikace a přenos dat přes MQTT broker byly zvoleny kvůli své jednoduchosti a dostupnosti knihoven jak pro Python, tak pro ESP8266. Dokumentace knihoven je zde [7, 8].
<br />
  
### 2. Ukládání dat a práce s daty (MQTTCommunication2.0.py):
  
Data, která jsou publikována na MQTT broker, jsou sbírána pomocí skriptu MQTTCommunication2.0.py, který se subscribne na daný topic a následně vkládá data do pole slovníků. Při nasbírání definovaného množství vzorků jsou data uložena do csv souboru ve formě pandas DataFrame.
  
Při sběru dat v je vzhledem k dosahu signálu z Wi-Fi téměř jisté, že vždy budou v různých místech dostupné jiné AP. Z tohoto důvodu se v datech vyskytuje velké množství chybějících hodnot (NaN).
  
Chybějící hodnoty tvoří velký problém pro většinu modelů strojového učení, které s nimi neumí pracovat.  Metod, jak se s chybějícími daty vypořádat, je mnoho a základní způsoby jsou popsány zde [9] nebo zde [10].
  
Protože u W-Fi sítě je hlavním důvodem slabého signálu vzdálenost od AP, byly všechny chybějící hodnoty nahrazeny hodnotou -100 dBm, která má reprezentovat velmi slabý až nedostupný signál.
  
### 3. Trénování modelů (Train_w_scikit.py, Train_w_tf.py):
  
Po nasbírání dostatečného množství dat jsou využity knihovny Sci-kit learn [11] a Tensorflow  [12] pro natrénování modelů strojového učení. Určení konečného počtu poloh dobře koresponduje   s typem problému klasifikace. Při trénování bylo použito 5 různých algoritmů z knihoven Sci-kit learn a Tensorflow, které se pro klasifikaci hodí. 
<br />
<br />Tyto algoritmy jsou:
- KNN (K-nearest neighbors) – Algoritmus, který klasifikuje objekt na základě třídy jeho  nejbližších sousedů.
- SVM (Support Vector Machine) – Algoritmus, který se snaží najít nadrovinu, jež dobře rozdělí data podle různých kategorií. Nadrovina s maximální vzdáleností od nejbližšího bodu je vybrána. V nejjednodušší formě je SVM binarní klasifikátor a pro vyšší dimenze jich musí být vytvořeno víc.
-	DT (Decision tree) – Algoritmus, který klasifikuje objekt na základě několika vnořených if/else příkazů s podmínkami vytrénovanými tak, aby byly dosaženy “pure leaf nodes” (uzly, které jednoznačně nebo s dostatečnou přesností určí třídu). Algoritmus rozhoduje na základě entropie stavů. – NEBYL PŘI ŘEŠENÍ POUŽIT, UVEDEN POUZE PRO OBJASNĚNÍ FUNKCE RF
- RF (Random Forest) – Algoritmus skládající se z několika náhodných DT - každý jeden strom využívá jiné features při trénování. Predikce třídy jsou založeny například na četnosti hlasování jednotlivých stromů.
- NN (Neural Network) – Struktura tvořená souborem neuronů (kontejnerů držících nějaké číslo), které jsou poskládány do vrstev. Neurony z jedné vrsty jsou propojené s neurony vrstvy následující, přičemž propojení má určitou váhu, která je dána natrénováním modelu. Hodnota neuronu je dána aplikací aktivační funkce na váženou sumu hodnot předchozích neuronů s přičtenou natrénovanou konstantou zvanou bias.
  
Zdrojů zabývajících se danými algoritmy je mnoho, například [13-17], za zmínku také stojí 2 interaktivní zdroje [18, 19]. 
### 4. Predikce v reálném čase (RealTimeLocation.py):
  
Poslední částí práce je program, který umí využít natrénované modely a v reálném čase zobrazovat, kde se deska ESP8266 nachází. K tomu byla využita knihovna PySide6. Hlavním nedostatkem této části je to, že model neumí zobrazovat pozici v případě, kdy narazí na novou Wi-Fi síť, kterou při trénování nezachytil. Je to způsobeno tím, že klasifikátory umí pracovat pouze s předem natrénovaným množstvím features.
  
Řešením by mohlo být:
  1. Použít klasifikátor, kterému různé množství features nevadí
  2. Využívat jen předem jasně dané sítě a s ostatními vůbec nepracovat
  3. Předzpracovat data před predikcí
  
## Dosažené výsledky
Bylo zvoleno 5 poloh/místností, ve kterých byla měřena data. Při prvotním natrénovaní modelů nebylo dosaženo požadovaných výsledků. Nasbíraná data byla plná hodnot NaN kvůli tomu, že se velké množství AP nacházelo daleko a jejich signál bylo možné zachytit jen výjimečně – u některých například i méně než 10krát z 600 naměřených hodnot. Pouze ze 3 AP byly signály získávány pravidelně. Většina použitých klasifikátorů dosahovala přesnosti okolo 70%.
  
Aby se výsledky zlepšily, byl přidán AP do jedné z místností. Díky této změně se dosažené výsledky výrazně zlepšily a přesnost klasifikátorů se začala pohybovat okolo 95%
  
<br />
  
## Použité zdroje
[1] https://arduino-esp8266.readthedocs.io/en/latest/esp8266wifi/readme.html
  
[2] https://en.wikipedia.org/wiki/Network_address_translation
  
[3] https://portforward.com/how-to-port-forward/
  
[4] https://en.wikipedia.org/wiki/Universal_Plug_and_Play
  
[5] https://bford.info/pub/net/p2pnat/
  
[6] https://www.youtube.com/watch?v=WmKAWOVnwjE&ab_channel=OptoVideo
  
[7] https://github.com/knolleary/pubsubclient
  
[8] https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php
  
[9] https://www.analyticsvidhya.com/blog/2021/10/handling-missing-value/
  
[10] https://stats.stackexchange.com/questions/23456/dealing-with-datasets-with-a-variable-number-of-features
  
[11] https://scikit-learn.org/stable/
  
[12] https://www.tensorflow.org/
  
[13] https://scikit-learn.org/stable/tutorial/basic/tutorial.html
  
[14] https://en.wikipedia.org/wiki/Support-vector_machine
  
[15] https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm
  
[16] https://en.wikipedia.org/wiki/Random_forest
  
[17] https://en.wikipedia.org/wiki/Artificial_neural_network
  
[18] https://playground.tensorflow.org/#activation=tanh&batchSize=10&dataset=circle&regDataset=reg-plane&learningRate=0.03&regularizationRate=0&noise=0&networkShape=4,2&seed=0.70949&showTestData=false&discretize=false&percTrainData=50&x=true&y=true&xTimesY=false&xSquared=false&ySquared=false&cosX=false&sinX=false&cosY=false&sinY=false&collectStats=false&problem=classification&initZero=false&hideText=false
  
[19] https://poloclub.github.io/cnn-explainer/
