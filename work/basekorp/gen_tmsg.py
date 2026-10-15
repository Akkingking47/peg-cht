# -*- coding: utf-8 -*-
"""BASEKORP `.tmsg`（任务目标提示电文）译文装配器。

输入 work/basekorp/basekorp-tmsg-export.tsv（tmsg.py export 产出）
输出 work/basekorp/basekorp-tmsg.tsv（file / src / dst，供 tmsg.py apply）

铁律（work/tmsg/tmsg.py 文档）：
  1. 首尾连续 CRLF 段是屏幕定位/清屏指令，必须逐字节保留 —— 本脚本不碰，交给 tmsg.py。
  2. 正文按 CP1252 读原文、按 GBK 写译文（tmsg.py 的 build() 已处理）。
  3. 密码/乱码电文（---AGFB…---）是**刻意伪装的密文**，不译。
  4. 电文里引用的**部队名**必须与 .xscn 已译名完全一致，否则玩家找不到该部队
     （如 `'HQ CCB/1ArmDiv'` -> `'司令部战斗指挥部B/第1装甲师'`）。
"""
import io, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'basekorp-tmsg-export.tsv')
OUT = os.path.join(HERE, 'basekorp-tmsg.tsv')

# ---------------------------------------------------------------- 逐行译文
T = {
# —— 情报通报：X 已抵达（模板句，第N一律前置）
'Intelligence report: Luftwaffe reinforcements arrived.': '情报通报：德国空军增援部队已抵达。',
'Intelligence report: Pionier-Bataillon 627 arrived.': '情报通报：第627工兵营已抵达。',
'Intelligence report: Parts of 29th SS-Grenadier-Division arrived.': '情报通报：党卫军第29掷弹兵师部分部队已抵达。',
'Intelligence report: Parts of 26th Infantry-Division arrived.': '情报通报：第26步兵师部分部队已抵达。',
'Intelligence report: Submarine U-104 arrived.': '情报通报：潜艇U-104已抵达。',
'Intelligence report: 4th Panzer-Division and Luftwaffe reinforcements arrived.': '情报通报：第4装甲师与德国空军增援部队已抵达。',
'Intelligence report: 8th Infantry-Division arrived.': '情报通报：第8步兵师已抵达。',
'Intelligence report: Infantry-Regiment Großdeutschland arrived.': '情报通报：大德意志步兵团已抵达。',
'Intelligence report: Pionier-Bataillon 41 arrived.': '情报通报：第41工兵营已抵达。',
'Intelligence report: Italian cruiser Eugenio di Savoia arrived.': '情报通报：意大利巡洋舰“欧根尼奥·迪·萨伏依”号已抵达。',
'Intelligence report: Italian cruiser Gorizia arrived.': '情报通报：意大利巡洋舰“戈里齐亚”号已抵达。',
'Intelligence report: Parts of 15th Panzer-Division arrived.': '情报通报：第15装甲师部分部队已抵达。',
'Intelligence report: Iranian 8th Engineer-Bataillon arrived.': '情报通报：伊朗第8工兵营已抵达。',
'Intelligence report: Iranian Regiment-size combat group arrived.': '情报通报：伊朗团级战斗群已抵达。',
'Intelligence report: Pionier-Landungs-Bataillons arrived.': '情报通报：工兵登陆营已抵达。',
'Intelligence report: Iranian Patrol Crafts arrived.': '情报通报：伊朗巡逻艇已抵达。',
'Intelligence report: Romanian 4th Mountain-Division arrived.': '情报通报：罗马尼亚第4山地师已抵达。',
'Intelligence report: Brigade-size combat group arrived.': '情报通报：旅级战斗群已抵达。',
'Intelligence report: Regiment-size combat group arrived.': '情报通报：团级战斗群已抵达。',
'Intelligence report: Slovakian Regiment-size combat group and Air Force reinforcements arrived.': '情报通报：斯洛伐克团级战斗群及空军增援部队已抵达。',
'Intelligence report: Patrol Crafts arrived.': '情报通报：巡逻艇已抵达。',
'Intelligence report: 100th light Infantry-Division arrived.': '情报通报：第100轻步兵师已抵达。',
'Intelligence report: 3rd Panzer-Division arrived.': '情报通报：第3装甲师已抵达。',
'Intelligence report: 29th Infantry-Division (mot.) arrived.': '情报通报：第29步兵师(摩托化)已抵达。',
'Intelligence report: 23th Panzer-Division arrived.': '情报通报：第23装甲师已抵达。',
'Intelligence report: Hungarian 1st Armored Field Division and Luftwaffe reinforcements arrived.': '情报通报：匈牙利第1装甲野战师及德国空军增援部队已抵达。',
'Intelligence report: Panzerzug 26 arrived.': '情报通报：第26装甲列车已抵达。',
'Intelligence report: 10th SS-Panzergrenadier-Division arrived.': '情报通报：党卫军第10装甲掷弹兵师已抵达。',
'Intelligence report: 31th Infantry-Division arrived.': '情报通报：第31步兵师已抵达。',
'Intelligence report: Italian 3rd Mobile Division arrived.': '情报通报：意大利第3摩托化师已抵达。',
'Intelligence report: Regia Aeronautica reinforcements arrived.': '情报通报：意大利皇家空军增援部队已抵达。',
'Intelligence report: Schwere Panzer-Abteilungen 503 and 507 arrived.': '情报通报：第503、第507重装甲营已抵达。',
'Intelligence report: Italian battleship Littorio and cruiser Bolzano arrived.': '情报通报：意大利战列舰“利托里奥”号与巡洋舰“博尔扎诺”号已抵达。',
'Intelligence report: Battleship group arrived.': '情报通报：战列舰编队已抵达。',
'Intelligence report: Aircraft carrier group arrived.': '情报通报：航空母舰编队已抵达。',
'Intelligence report: U-Boat Flotilla arrived.': '情报通报：U艇支队已抵达。',
'Intelligence report: 18th Panzergrenadier-Division arrived.': '情报通报：第18装甲掷弹兵师已抵达。',
'Intelligence report: Hungarian 2nd Armored Division arrived.': '情报通报：匈牙利第2装甲师已抵达。',
'Intelligence report: Parts of 22th Infantry-Division (LL) arrived.': '情报通报：第22步兵师(空降)部分部队已抵达。',
'Intelligence report: Marine Kommandos have arrived. Capture the Port of Algiers.': '情报通报：海军突击队已抵达。攻占阿尔及尔港。',

# —— 情报通报：警戒 / 自由文本
'Intelligence report: Attention, enemy tank forces advance from the north towards Portsmouth and will arrive shortly!': '情报通报：注意，敌军装甲部队正从北面向朴次茅斯推进，即将抵达！',
'Intelligence report: Attention, enemy infantry forces advance from the north towards Portsmouth and will arrive shortly!': '情报通报：注意，敌军步兵部队正从北面向朴次茅斯推进，即将抵达！',
'Intelligence report: Attention, enemy forces advance from the north towards Portsmouth and will arrive shortly!': '情报通报：注意，敌军正从北面向朴次茅斯推进，即将抵达！',
'Intelligence report: Attention, enemy landings at the airfield south of Astrakhan and the eastern Volga River banks are imminent!': '情报通报：注意，敌军即将在阿斯特拉罕以南的机场和伏尔加河东岸登陆！',
'Intelligence report: Attention, an enemy tanks division approaches from the east towards Jesup!': '情报通报：注意，敌军一个坦克师正从东面向杰瑟普逼近！',
'Intelligence report: It seems an fearsome reputation run ahead your troops - there was a mass surrender in Sverdlovsk! Keep a corridor open that the POW columns can be quickly led away to the west and not impede further combat operations!': '情报通报：看来你的部队恶名远扬——斯维尔德洛夫斯克发生了大规模投降！保持一条通道畅通，让战俘纵队能迅速向西押送，以免妨碍后续作战！',
'Intelligence report: The Japanese arrived! Japanese troops approach from the east to take Omsk in a pincer.': '情报通报：日军来了！日军正从东面逼近，要以钳形攻势夺取鄂木斯克。',
'Intelligence report: The train tracks were blown up by partisans! Pionier-Bataillon 571 is sent to carry out the necessary repairs and Panzerzug 34 is accompanies to protect the Pioniers.': '情报通报：铁路被游击队炸毁！第571工兵营奉命前往抢修，第34装甲列车随行掩护工兵。',
'Intelligence report: The Finns have decided to participate in our attack. They are broken through the Soviet defense line in the north. All incoming Finnish units are under your command.': '情报通报：芬兰人已决定参加我方的进攻。他们在北面突破了苏军防线。所有陆续抵达的芬兰部队均归你指挥。',
'Intelligence report: Parts of the Research Facility could be occupied by commando units. Make sure that the enemy does not manage to destroy the building!': '情报通报：突击队可能已占领研究设施的一部分。务必确保敌人无法摧毁该建筑！',
'Intelligence report: U.S. forces attack French Martinique. Take action!': '情报通报：美军正在进攻法属马提尼克。采取行动！',
"Intelligence report: We're too late, the invasion has already begun. Try to protect the sea transports with your Air Force. Reinforcements is on the way!": '情报通报：我们来晚了，登陆已经开始。设法用你的空军掩护海上运输船队。增援部队正在路上！',

# —— 司令部通报 / 增援抵达（无 Intelligence report 前缀）
'HQ sends informations regarding imminent Soviet counterattacks towards Logovsk (16,1)  and towards the rail bridge from the North-East.': '司令部通报：苏军即将对洛戈夫斯克(16,1)以及东北方向的铁路桥发动反击。',
'HQ sends the german 20th Pz Div as reinforcements. The column will arrive in Roman (7,24) soon.': '司令部派出德国第20装甲师增援。纵队即将抵达罗曼(7,24)。',
'HQ sends German 13th Pz Div as reinforcements. The column will arrive around (2,19) soon.': '司令部派出德国第13装甲师增援。纵队即将抵达(2,19)一带。',
'HQ sends informations regarding an imminent enemy counterattack towards Carei (7,9) from the North-West . Prepare yourself .': '司令部通报：敌军即将从西北方向对卡雷伊(7,9)发动反击。做好准备。',
'Elements of the 5th Pz Division arrive at your Northern flank.': '第5装甲师的部分部队抵达你的北翼。',
'The 7th Infantry Division arrives from the South.': '第7步兵师从南面抵达。',
'The 5th Pz Division has arrived to strengthen your attack. No further reinforcements are expected.': '第5装甲师已抵达以加强你的攻势。预计不会再有增援。',
'11th and 8th  Panzer Divisions are approaching Belgrade from the West and South.': '第11装甲师与第8装甲师正从西面和南面逼近贝尔格莱德。',
'The Aufklaerungsabteilung of the 10th Motorized Infantry Division arrives North of your forces. The bulk of the division will be available for action tomorrow (2 days from now).': '第10摩托化步兵师的侦察营抵达你的部队以北。师主力将于明日(2天后)投入行动。',
'The Aufklaerungsabteilung of the 7th Panzer Infantry Division arrives South of your forces. The bulk of the division will be available for action tomorrow (2 days from now).': '第7装甲步兵师的侦察营抵达你的部队以南。师主力将于明日(2天后)投入行动。',
'Move the unit in the SE corner to deploy your core forces.': '调动东南角的部队，以展开你的核心兵力。',
'The first elements of the 258th Infantry Division arrive in the South. The full division will be available to execute your orders within 36 hours (3 turns).': '第258步兵师的先头部队抵达南面。全师将在36小时(3回合)内听候你的调遣。',
'III/StG77 and I/JG51 are available to support your attack.': '第77俯冲轰炸机联队第3大队与第51战斗机联队第1大队可支援你的进攻。',

# —— 工兵 / 架桥 / 守点（部队名口径：本单位/上级/再上级）
'The Pioneers of II/20/10th Mot Inf(XXIV) have arrived on the battlefield use them to build a forward air base.': '第10摩托化步兵师(第24军)第2/第20营的工兵已抵达战场，用他们修建前方空军基地。',
'The Pioneers of III/23/23rd Inf(Res)(XIX) have arrived on the battlefield, use them to build a forward Air Base.': '第23步兵师(预备队)(第19军)第3/第23营的工兵已抵达战场，用他们修建前方空军基地。',
'Use I/25/2nd Inf(Res)(XIX) to hold Airfield.': '用第2步兵师(预备队)(第19军)第1/第25营守住机场。',
'Use II/25/2nd Inf(Res)(XIX) to hold Montcornet.': '用第2步兵师(预备队)(第19军)第2/第25营守住蒙科尔内。',
'The Bridging Pioneers of III/34/34th Inf(XII) have arrived on the battlefield, use them to build Pontoon bridges over the River Bug and River Machawic at the 2 hexes marked (Bridge).': '第34步兵师(第12军)第3/第34营的架桥工兵已抵达战场，用他们在布格河与马哈维茨河上标有(桥梁)的2格处架设浮桥。',
'The Pioneers of III/31/31st Inf(XII)  have arrived on the battlefield, use them to build a forward Air Base.': '第31步兵师(第12军)第3/第31营的工兵已抵达战场，用他们修建前方空军基地。',
'The Pioneers of III/293/293rd Inf(XXXV) have arrived on the battlefield, use them to construct a forward airbase.': '第293步兵师(第35军)第3/第293营的工兵已抵达战场，用他们修建前方空军基地。',

# —— 柯尼斯堡 / 日耳曼第3军
'Lead elements of III germanische Korps are now 80 Km North-East of Königsberg, 60km from the rendezvous point.': '日耳曼第3军的前锋部队现位于柯尼斯堡东北80公里处，距会合点60公里。',
'The newly formed 82nd Volkssturm Abteilung is ready for action in Königsberg. Lead elements of III germanische Korps are now 70 Km North-East of Königsberg, 50km from the rendezvous point.': '新编成的第82国民突击队营已在柯尼斯堡做好行动准备。日耳曼第3军的前锋部队现位于柯尼斯堡东北70公里处，距会合点50公里。',
'Lead elements of III germanische Korps are now 60 Km North-East of Königsberg, 40km from the rendezvous point.': '日耳曼第3军的前锋部队现位于柯尼斯堡东北60公里处，距会合点40公里。',
'The newly formed 97th Volkssturm Abteilung is ready for action in Königsberg. Lead elements of III germanische Korps are now 50 Km North-East of Königsberg, 30km from the rendezvous point.': '新编成的第97国民突击队营已在柯尼斯堡做好行动准备。日耳曼第3军的前锋部队现位于柯尼斯堡东北50公里处，距会合点30公里。',
'Lead elements of III germanische Korps are now 40 Km North-East of Königsberg, 20km from the rendezvous point.': '日耳曼第3军的前锋部队现位于柯尼斯堡东北40公里处，距会合点20公里。',
'The newly formed Hitler Jugend Volkssturm Abteilung is ready for action in Königsberg. Elements of Sturm Geschwader 3 are called in to clear increasing Soviet resistance in front of the advancing III germanische SS Korps.': '新编成的希特勒青年团国民突击队营已在柯尼斯堡做好行动准备。第3突击航空联队奉召前来，清除推进中的党卫军第3日耳曼军当面日益增强的苏军抵抗。',
'Lead elements of III germanische Korps are now facing heavy resistance 30 Km North-East of Königsberg, 10km from the rendezvous point.': '日耳曼第3军的前锋部队现位于柯尼斯堡东北30公里处并遭遇顽强抵抗，距会合点10公里。',
'Lead elements of 11. SS-Freiwilligen-Panzergrenadier-Division Nordland and SS-Freiwilligen-Panzer-Grenadier-Brigade Nederland have arrived at the rendezvous point.': '党卫军第11“北地”志愿装甲掷弹兵师与党卫军“尼德兰”志愿装甲掷弹兵旅的前锋部队已抵达会合点。',

# —— 北非 / 突尼斯
'D/509P.I.Bn. was dropped SE of Lourmel (controlled by the AI).': '第509伞降步兵营D连空投于卢尔梅尔东南(由电脑控制)。',
'36th Brigade group has run into a German attack supported by armour. Intelligence could not have been more wrong.': '第36旅级战斗群遭遇了有装甲支援的德军进攻。情报错得不能再错了。',
'It looks like the armour supporting XI.Pionier Abteilung has been withdrawn.': '看来支援第11工兵营的装甲部队已被撤走。',
'Elements of the  97th US Bombardment Group are available for one mission.': '美国第97轰炸机大队的部分兵力可执行一次任务。',
'The first elements of the 14th Fighter Group have been moved closer to the front.': '第14战斗机大队的先头部队已前移靠近前线。',
"The US 5th Field Artillery Battalion of the 1st US Infantry Division and the remainder of Combat Command B arrive from Oran. Move the 'HQ CCB/1ArmDiv' unit to deploy the rest of your core.": '美国第1步兵师第5野战炮兵营及B战斗司令部余部自奥兰抵达。调动“司令部战斗指挥部B/第1装甲师”部队以展开你剩余的核心兵力。',
'The British 2nd Parachute Infantry Battalion drops at Oudna - South of Tunis. The British 1st Commando Battalion lands West of Bizerte.': '英国第2伞降步兵营在突尼斯以南的乌德纳空降。英国第1突击营在比塞大以西登陆。',
'26 Infantry Combat Team of the 1st US Infantry Division arrives close to Ousseltia.': '美国第1步兵师第26步兵战斗队在乌塞尔提亚附近抵达。',
'Elements of the 250th Fighter Group / 12th Air Force are available.': '第12航空队第250战斗机大队的部分兵力可供调遣。',
'II Corps HQ have sent a battalion of 1US Inf Div to your aid.': '第2军司令部已调美国第1步兵师一个营前来支援你。',
'II Corps HQ have sent another battalion of 1US Inf Div to your aid.': '第2军司令部又调美国第1步兵师一个营前来支援你。',
'The Brits have sent Gore force - a composite battalions of the 26th Armoured Brigade - to help blocking the road to Thala.': '英国人派出了戈尔分队——由第26装甲旅混编的数个营——协助封锁通往塔莱的公路。',
'The Royal Air Force has directed two Squadrons to your sector. The British 6th Armoured Division has sent an armoured battalion of the 26th Armoured Brigade to help blocking the road to Thala.': '皇家空军已调两个中队前往你的防区。英国第6装甲师派出第26装甲旅一个装甲营协助封锁通往塔莱的公路。',
'The British 6th Armoured Division has sent another armoured battalion of the 26th Armoured Brigade to help blocking the road to Thala.': '英国第6装甲师又派出第26装甲旅一个装甲营协助封锁通往塔莱的公路。',
'The British have sent an infantry battalion to help blocking the road to Thala.': '英国人派出一个步兵营协助封锁通往塔莱的公路。',
"P38's of 18th Fighter Group are available for action.": '第18战斗机大队的P-38战斗机可投入行动。',
'The British 6th Armoured Division has sent an armoured battalion of the 26th Armoured Brigade to help blocking the road to Thala. The battalion is partly equiped with new Sherman tanks.': '英国第6装甲师派出第26装甲旅一个装甲营协助封锁通往塔莱的公路。该营部分装备了新型谢尔曼坦克。',

# —— 大西洋 / 不列颠
'---from BdU to U-47---sail to grid X35---free for further operations---': '---潜艇部队司令致U-47---驶往X35坐标格---可自由执行后续任务---',
'"My name is Devlin, Mr. Devlin.  At your service sir!"': '“我叫德夫林，德夫林先生。愿为您效劳，长官！”',
'We questioned a local fisherman and he reported incomming british ships from the east.': '我们审问了一名当地渔民，他报告说有英国舰船正从东面驶来。',
'As soon as you take the Airport, HQ will send you a fighter.': '你一拿下机场，司令部就会派给你一架战斗机。',
'Allied destroyers are entering the Ofotfjord!': '盟军驱逐舰正在进入奥福特峡湾！',
'Thousands of spectators watch you leaving the port. There are many spys around...It seems the enemy is informed about every of your steps.': '成千上万的围观者目送你离开港口。周围有许多间谍……敌人似乎对你的一举一动都了如指掌。',
'Your radio room recives a lot of coded radio transmissions.': '你的报务室收到大量加密无线电通信。',
'Is that smoke? In the east!': '那是烟吗？在东面！',
'HQ sends you a tank as addition to your core.': '司令部拨给你一辆坦克，补充你的核心部队。',
'A convoy of motorized units arrives from Le Havre.': '一支摩托化部队车队自勒阿弗尔抵达。',
'Our italian friends are sending us some reinforements.': '我们的意大利朋友正给我们派来一些增援。',
'Long range recon flights reveal two larg british fleets in the northeast. Get your ships ready for the fight!': '远程侦察飞行发现东北方向有两支庞大的英国舰队。让你的舰艇做好战斗准备！',
'We found documents in a improvised shelter in the woods. It seems there are hidden fuel depots in Villages called Chilham and Waltham.': '我们在树林里一处临时掩体中发现了文件。看来奇尔哈姆和沃尔瑟姆两个村庄里藏有燃料库。',
'The Maunsell Forts in the shallow waters of the Thames Estuary are a severe threat to our planes and ships. They are heavily fortified and still maned.': '泰晤士河口浅水区的毛恩塞尔堡垒对我们的飞机和舰艇构成严重威胁。它们防御坚固，且仍有驻守。',
'If you take Billericay in time, HQ will send you a prototype unit.': '如果你及时拿下比勒里基，司令部会派给你一支试验部队。',
'The little remainder of the royal navy should be somewhere around.': '皇家海军残存的少量舰艇应该就在附近一带。',

# —— 东线 / 杂项
'This is your last chance to decisively defeat the Belgians or this war could drag on for months. Hurry up and show some initiative.': '这是你决定性击败比利时人的最后机会，否则这场战争可能拖延数月。抓紧行动，拿出点主动性来。',
'Soviets are coming!': '苏军来了！',
'Many enemy tanks nearly drowned in the swamp! Capture them!': '许多敌军坦克差点陷没在沼泽里！把它们缴获过来！',
'Urgent message for all troops: "There have been reports of Russkie scientists experimenting with their troops to create "mutant" soldiers.': '全体部队紧急通报：“有报告称俄国科学家用自己的士兵做实验，制造‘变异’士兵。',
'Caution, our spies have discovered the Yankees have perfected their own "super bomb" and will use it against us.': '注意，我方间谍发现美国佬已完善了他们自己的“超级炸弹”，并将用它来对付我们。',
'Saboteurs have blown our supply lines and bases!': '破坏分子炸毁了我们的补给线和基地！',
'You have been given a heavy railgun to assist your advance.': '你获得了一门重型列车炮以支援推进。',
'The enemy has blown our supply hex but this should not slow us down!': '敌人炸掉了我们的补给格，但这不该拖慢我们的速度！',
'Those damn frogs have blown the bridges and the airfield.': '那些该死的法国人炸毁了桥梁和机场。',
'Watch out for the stampeding elephants, they have been loaded with explosives!': '当心那些狂奔的大象，它们身上驮满了炸药！',
'The Spanish fanatics are determined for Spain to have influence in Algiers. Use the fanatical volunteers to demolish the ports and hinder resupplies.': '这些西班牙狂热分子决意让西班牙在阿尔及尔拥有影响力。用这些狂热的志愿者摧毁港口并阻碍补给。',
'HQ has estabished fuel reserves at Brest.': '司令部已在布雷斯特建立燃料储备。',
'Those damn Russkies must have known about our fuel depot plans and have counter-attacked at our weak point!': '那些该死的俄国人一定早就知道我们的燃料库计划，并在我们的薄弱点发动了反击！',
'Brest-Litosvk has been completey devastated! You must remove the threat of Russian troops behind our lines!': '布列斯特-立托夫斯克已被彻底摧毁！你必须消除我军后方俄军的威胁！',
'Damn,  the Russkies are burning their own city in an attaempt to slow us down!': '该死，俄国人在焚烧他们自己的城市，企图拖慢我们！',
'Bloody hell! The russians had explosives setup as boobytraps all over the city!': '该死！俄国人在全城布设了饵雷！',
'The russians have launched a counter-attack in the south-east quandrant. Defend your rear flank from this attack.': '俄军在东南象限发动了反击。守住你的后方侧翼，挡住这次进攻。',
}

# 刻意伪装的密文：不译（改动会破坏场景氛围，且不是自然语言）
KEEP = {
    '---AGFB HFHG JFUG NHGM JGHD JFHG OPFH BDHG SHDG JFHF KDGH---',
    "---No Man'sHCVCHIOC---proto-HXCSLYHS---B1------GPISXYWQ---........",
}


def main():
    rows = [l.rstrip('\n').split('\t') for l in io.open(SRC, encoding='utf-8')][1:]
    need = collections.Counter()
    for r in rows:
        for ln in r[5].split('<CRLF>'):
            s = ln.strip()
            if s:
                need[s] += 1
    print('唯一行 %d / 实例 %d' % (len(need), sum(need.values())))
    miss = [s for s in need if s not in T and s not in KEEP]
    if miss:
        print('!! 未覆盖 %d 条：' % len(miss))
        for s in miss:
            print('   %r' % s)
        raise SystemExit(1)

    # 逐文件重建正文（保留原文的空行结构：空行原样留空）
    out = []
    nfile = 0
    for r in rows:
        fn, body = r[0], r[5]
        if not body.strip():
            continue
        parts = []
        for ln in body.split('<CRLF>'):
            s = ln.strip()
            if not s:
                parts.append('')
            elif s in KEEP:
                parts.append(s)
            else:
                parts.append(T[s])
        out.append((fn, body.replace('<CRLF>', '\r\n'), '\r\n'.join(parts)))
        nfile += 1

    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write('file\tsrc\tdst\r\n')
        for fn, src, dst in out:
            f.write('%s\t%s\t%s\r\n' % (fn, src.replace('\r\n', '<CRLF>'),
                                        dst.replace('\r\n', '<CRLF>')))
    print('译文表 %d 条（文件 %d）-> %s' % (len(out), nfile, OUT))
    nz = sum(1 for _, _, d in out if any('\u4e00' <= ch <= '\u9fff' for ch in d))
    print('  含汉字 %d / 无汉字（密文）%d' % (nz, len(out) - nz))


if __name__ == '__main__':
    main()
