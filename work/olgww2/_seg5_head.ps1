$ErrorActionPreference='Stop'
$SRC='D:\OpenPG2\EFILE_OLGWW2\SCENARIO\'
$DST='D:\DSH\军事游戏汉化\work\olgww2\scenario\'
$seg='D:\DSH\军事游戏汉化\work\olgww2\segments.txt'

$all=Get-Content -LiteralPath $seg
$s=($all|Select-String -SimpleMatch '### SEGMENT 5').LineNumber
$e=($all|Select-String -SimpleMatch '### SEGMENT 6').LineNumber
$NAMES=@($all[$s..($e-2)]|Where-Object{$_.Trim() -ne ''})
"files: $($NAMES.Count)"

# ---------------------------------------------------------------- phrases
$P='(?<![A-Za-z]){0}(?![A-Za-z])'
$PH=@(
 'I can''t understand your failure commander.  It seems our estimation of your skills were wrong... the central ChCP commission has demoted you to a private for the remainder of the fighting.  This should erase any capitalist bad manners that you may have acquired.|指挥官，我无法理解你的失败。看来我们对你的能力评估有误……中共中央已把你贬为列兵，直至战斗结束。这应该能洗掉你可能沾染上的资产阶级习气。',
 'Our battle against the ancient landlords of oppression has been suddenly stopped... now we must again dress ourselves as peasants to avoid being captured by the enemy.|我们反抗古老压迫者地主的战斗突然中断了……现在我们只能再次装扮成农民，以免被敌人抓住。',
 'Congratulations, the way to the South is open.  The North Americans have received a stinging lesson on the power of the People''s War.|恭喜，南下的大门已经打开。北美人尝到了人民战争威力的沉痛教训。',
 'Ahh, comrade Commander!  Do you like Khabarovsk?  It''s a pretty city, isn''t it?   I know you are the greatest hero of the PRC and the KRC and I have a mission for you from the Kremlin.  I have to give you a letter from Moscow but... well anyway this is a good situation to do it.  Err... yes, but first, let''s negotiate the surrender of my forces in this sector.|啊，指挥官同志！你喜欢哈巴罗夫斯克吗？这城市很漂亮，不是吗？我知道你是中华人民共和国和朝鲜民主主义人民共和国最伟大的英雄，克里姆林宫交给你一项任务。我要转交一封莫斯科的来信，但……算了，总之眼下正是好时机。呃……对，不过先让我们谈一谈本地段我军的投降事宜。',
 'Wan Shan!  We have saved a lot of our men from the Kuomingtan onslaught.  We must hope to counterstrike the dirty nationalists as soon as we receive some Soviet aid through Manchuria.|万岁！我们从国民党的猛攻中救出了大量人员。只盼一俟通过满洲获得苏联援助，就立刻对肮脏的国民党反动派发起反击。',
 'Wan shan!  All the mission objectives were achieved before the Japanese could send reinforcements to this area.  Now your task is to hide your guerrillas and wait for new orders.|万岁！所有任务目标均已在日军向该地区派出增援之前达成。现在你的任务是隐蔽游击队，等待新的命令。',
 'Tong gan ku!  The dirty Japanese invaders got a lesson in good old ancient Chinese tactics.  The enemy division is completely scattered and our troops can continue to harass them.|同甘苦！肮脏的日本侵略者领教了中国古老战术的厉害。敌军师已被彻底打散，我军可以继续袭扰他们。',
 'Wan shan!  The KMT have suffered a great defeat.  I''m sure we will be celebrating our victory over Chiang Kai Shek''s troops during the coming year of 1948.|万岁！国民党遭到了惨败。我相信到1948年，我们就会庆祝对蒋介石军队的胜利。',
 'Thanks to your good work, our base at Linjiang is now safe.  In addition, we are now in a good position to attack Changchun, Jilin and Siping during the next summer offensive.  We will wait for good weather to arrive in Manchuria.|多亏你干得出色，我们的临江根据地现已安全。此外，我们目前处于有利态势，可在下一次夏季攻势中进攻长春、吉林和四平。我们将等待满洲好天气的到来。',
 'Congratulations!, Changchun, Jilin and Siping have been captured. This will be a big problem for the Nationalists, since their communications by train or by road from Manchuria to Beijing are now stopped.|恭喜！长春、吉林和四平已被攻占。这对国民党来说是个大麻烦，因为他们从满洲经铁路或公路通往北平的交通线现在已被切断。',
 'Victory!   We have crossed that damned bridge and many comrades have died, but their lives were not lost, they have contributed to the success of our retreat to save the Revolution.  Congratulations for your actions.|胜利！我们越过了那座该死的桥，许多同志牺牲了，但他们的生命没有白费，他们为我们成功撤退、挽救革命作出了贡献。祝贺你的行动。',
 'Wan Shan!  Did you see how the capitalists are escaping from us??   Pyongyang is again a communist stronghold, and we must continue to pursue and annihilate the UN forces.|万岁！你看到资本家们是怎么从我们面前逃跑的吗？？平壤重新成为共产主义据点，我们必须继续追击并歼灭联合国军。',
 'Congratulations on your victory.   Myself, together with Mao and our Komintern advisor Li-De (Otto Braun) are planning the evacuation of Jinggangshan.  We will do it quickly while the KMT troops are busy dealing with the Japanese in Manchuria.|祝贺你取得胜利。我正在同毛泽东以及我们的共产国际顾问李德（奥托·布劳恩）筹划撤离井冈山。我们要趁国民党军队忙于应付满洲的日军之机迅速行动。',
 'Congratulations comrade!  You are the new Premier of the People''s Republic of China. Mao has disappeared and we know he won''t be back, hahaha!  I hope your understanding of the communist doctrine will be the correct one.  That would be the best for the communist world.|恭喜你，同志！你已是中华人民共和国的新总理。毛泽东已经消失，我们知道他不会再回来了，哈哈哈！希望你对共产主义学说的理解是正确的。那对共产主义世界来说再好不过。',
 'The uprising was successful and Nanchang is ours!  This has become the first major stronghold of Marxism in China.  Now it is time to create a Revolutionary Committee in this city to manage our goals.  We must get Soviet aid by sea with another uprising in Guangzhou.  Our comrades there will receive our support from Nanchang.|起义成功了，南昌是我们的了！这里已成为马克思主义在中国的第一个重要据点。现在该在这座城市里成立革命委员会来掌管我们的目标。我们必须通过广州的另一次起义取得苏联的海上援助。那里的同志将从南昌得到我们的支援。',
 'The enemy offensive has been completely defeated.  Seoul is now securely in our hands, Kim-Il-Sung is really happy with your actions.  Now, let''s complete the communist victory in Korea.|敌人的攻势已被彻底粉碎。汉城现已稳稳掌握在我们手中，金日成对你的行动非常满意。现在，让我们完成共产主义在朝鲜的胜利。',
 'Xion wei!   The uprising was very successfull here in Changsha... Mao isn''t as popular as he wanted... but his prestige continues to grow anyway.   We are going to join his troops for now.|雄伟！长沙这里的起义非常成功……毛泽东并不像他自己希望的那样受欢迎……但他的声望仍在不断增长。我们暂时去与他的部队会合。',
 'Xion wei!   The uprising was successfull here in Changsha... Mao isn''t as popular as he wanted... but his prestige continues to grow anyway.   We are going to join his troops for now. |雄伟！长沙这里的起义非常成功……毛泽东并不像他自己希望的那样受欢迎……但他的声望仍在不断增长。我们暂时去与他的部队会合。',
 'Chiang Kai Shek has escaped from Taipei thanks to his American friends, but the whole Taiwanese island plus other minor islands are now part of the PRC.  The Civil War is over and all the Chinese territories are now unified under the red stars flag!  Comrade Mao is pleased with you, the hero of the PRC.|蒋介石靠他的美国朋友从台北逃走了，但整个台湾岛以及其他一些小岛现在都是中华人民共和国的一部分。内战结束了，全部中国领土如今在红星旗下获得统一！毛泽东同志对你很满意，你是中华人民共和国的英雄。',
 'This was a disaster!  The arguments formerly proposed by General McArthur have finally been accepted by Washington.  A nuclear attack was carried out over the city of Nanjing, killing millions of Chinese people.  The soviets have declined to give us any nuclear help and now we must accept the peace imposed by the West.|这是一场灾难！麦克阿瑟将军先前提出的主张最终被华盛顿采纳。核打击落在了南京市，数百万中国人民丧生。苏联拒绝给予我们任何核援助，现在我们只能接受西方强加的和平。',
 'This was a disaster... the arguments formerly proposed by General McArthur have finally been accepted by Washington.  A nuclear attack has been carried out over the city of Nanjing, killing millions of Chinese people... The soviets have declined to give us any nuclear help and now we must accept the imposed Western peace.|这是一场灾难……麦克阿瑟将军先前提出的主张最终被华盛顿采纳。核打击落在了南京市，数百万中国人民丧生……苏联拒绝给予我们任何核援助，现在我们只能接受西方强加的和平。',
 'Perfect!  The North Korean flag again flies over the city of Seoul.  Kim-Il-Sung is really pleased with you.   You have become a hero for the Korean people.   Anyway we are shortly going to open the negotiations with the UN forces to terminate this conflict.|好极了！朝鲜国旗重新飘扬在汉城上空。金日成对你非常满意。你已成为朝鲜人民的英雄。不过我们很快就要与联合国军开始谈判，以结束这场冲突。',
 'Perfect!  The North Korean flag again flies over the city of Seoul.  Kim-Il-Sung is really pleased with you.   You have become a hero for the Korean people.|好极了！朝鲜国旗重新飘扬在汉城上空。金日成对你非常满意。你已成为朝鲜人民的英雄。',
 'Now you are a hero for the People''s Republic of China and for all the workers around the world.|现在你是中华人民共和国的英雄，也是全世界工人的英雄。',
 'Congratulations comrade!  Korea is now entirely unified under the communist flag, and Kim-Il-Sung has been proclaimed chairman of the People''s Republic of Korea at Seoul. This is an enormous victory for the communist world, there have also been celebrations at other communist capitals like Moscow, East-Berlin, and of course Beijing.|恭喜你，同志！朝鲜如今已在共产主义旗帜下完全统一，金日成在汉城被宣布为朝鲜人民共和国主席。这是共产主义世界的巨大胜利，莫斯科、东柏林等共产主义国家首都也都举行了庆祝，北京当然也不例外。',
 'The uprising at Guangzhou against the local warlords was successful and access by sea for Soviet aid was secured.  Now, comrade Mao from Hunan is planning an assault on the city fortress of Changsha against the local warlords and KMT troops placed at that city. The central Chinese Communist Party director dislikes this operation, but we are going to dispatch your troops there to help our comrades in the offensive.  Personally, I don''t want the prestige of Mao Zedong to overly influence the ChCP.  He seems to gain more power each day.|广州反抗当地军阀的起义成功了，苏联援助的海上通道已经打通。现在，来自湖南的毛泽东同志正计划攻打长沙城，对付驻守该城的当地军阀和国民党军队。中共中央的领导不喜欢这次行动，但我们还是要把你的部队派去，在进攻中协助我们的同志。就我个人而言，我不希望毛泽东的声望对中共中央产生过大的影响。他似乎一天比一天更有权势。',
 'This is your duty commander; the 5th Japanese division is driving south towards the Pingxingguan Pass. You must block their path, and then, annihilate all the Japanese, using your famous guerrilla tactics.|这是你的任务，指挥官：日军第5师团正南下向平型关推进。你必须挡住他们的去路，然后用你著名的游击战术歼灭所有日军。',
 'As you know, we have signed an alliance with our former enemies, the nationalists.  Now, the enemy is the foreign imperialist invader, it''s time to forget our quarrel with the KMT for a while.  We are united with them against a common enemy: the Japanese Empire.  While the KMT troops are dealing with the Japanese armies in other parts of China, our guerrillas have been surrounded by the enemy advance in Manchuria and other many places in Northern China, and you (yes, you), a veteran ChCP commander will show the dirty invaders a bit of the people''s revolution power.  We must harass the Japanese rearguard as much as possible without taking too many losses.  I''m sure the current KMT-ChCP alliance will not long too much longer.|如你所知，我们已同从前的敌人国民党结成了同盟。如今敌人是外来的帝国主义侵略者，是时候暂时放下与国民党的争端了。我们与他们联合起来对付共同的敌人：日本帝国。当国民党军队在中国其他地区对付日军时，我们的游击队在满洲和中国北方许多地方被敌人的推进所包围，而你（没错，就是你），一位老练的中共指挥员，要让这些肮脏的侵略者见识一点人民革命的力量。我们必须尽可能袭扰日军后方，同时不要蒙受太大损失。我确信目前的国共同盟不会维持太久。',
 'Again, the central committee of the ChCP has agreed to launch another guerrilla assault on the Japanese rearguard in co-operation with our Kuomingtan ''allies''.  Comrade Mao dislikes this attack, but China is calling for Chinese action against the invaders, and that''s what we are going to carry out.  The main objectives must be the capture of enemy resources present in your area: the coal mines and factories.  Your battle plan includes some cities and don''t forget to cut all enemy lines of communication.|中共中央委员会再次同意与我们的国民党"盟友"合作，对日军后方发动又一次游击突袭。毛泽东同志不喜欢这次进攻，但中国在呼唤对侵略者采取中国式的行动，而这就是我们要去执行的。主要目标必须是夺取你所在地区的敌方资源：煤矿和工厂。你的作战计划包括若干城市，别忘了切断敌人所有的交通线。',
 'Act as quick as possible, the Japanese are going to use all available means to defeat any try to stop their penetration into China.|行动要尽可能迅速，日军将动用一切可用手段，粉碎任何阻止他们侵入中国的尝试。',
 'However, it''s still soon to enjoy our new training and equipment... the bad news?, well the mission of the US general George Marshall to pacificate China and reach an agreement between us and the KMT is a clear failure. The Kuomingtan have taken advantage of the time just to rearm their units, and now they are clearly taking positions around our areas, probably to anihilate us like in the 30''s. In case of the outbreak of the war... your mission is to drive your units in Wuhan to the West, to join the central ChCP units in Central China.|不过，现在享受我们的新训练和新装备还为时过早……坏消息呢？美国将军乔治·马歇尔调停中国、促成我们与国民党达成协议的使命彻底失败了。国民党只是利用这段时间重整了他们的部队，如今他们显然正在我们的根据地周围占据阵地，很可能想像30年代那样消灭我们。一旦战争爆发……你的任务是把你在武汉的部队向西调动，与中共中央在华中的部队会合。',
 'As you know, the Soviet victory agaisnt the Japanese in Manchuria the past year has opened the gate of the regular support of hardware and weapons to us. Now, the ChCP troops are better equipped and trained. The Soviets have given us some Japanese captured equipment from Manchuria, like tanks and artillery and the Japanese prisoners are training our brave men. They had no choice: work in Siberia or work with us!.|如你所知，去年苏联在满洲对日军的胜利，为我们打开了获得稳定武器装备支援的大门。现在，中共部队的装备和训练都更好了。苏联人把一些从满洲缴获的日军装备给了我们，比如坦克和火炮，日军俘虏正在训练我们勇敢的战士。他们别无选择：要么去西伯利亚干活，要么跟我们干！',
 'Nice to see you again... I hope the lessons you have reciently taken in the USSR about the modern warfare will be useful for us now. Well, please sit down, I have some information to bring you about the current situation.|很高兴再次见到你……希望你最近在苏联学的现代战争课程现在能对我们有用。好了，请坐，我有一些关于当前局势的消息要告诉你。',
 'Build your army, and cross the Yalu River to help the North Koreans and strike the UN forces.  Liberate Pyongyang to allow further advances to the 38 parallel and beyond.  We will have help from the air from our recently created People''s Liberation Army Air Force. Remember all the principles of the People''s War doctrine on your way.|组建你的军队，跨过鸭绿江去帮助朝鲜人民，打击联合国军。解放平壤，以便继续向三八线及其以南推进。我们最近组建的人民解放军空军将提供空中支援。行军途中要牢记人民战争学说的全部原则。',
 'Nice to see you again commander. Your next mission is highly secret and will take you to the Sino-Korean border.  The dirty North American invaders and their South Korean allies have smashed the North Koreans.  Kim-Il-Sung was close to a total victory during the past summer, but he didn''t protect his rearguard and as you know, the capitalist operation at Inch''on and Seoul has completely defeated the North Korean advance on Pusan.|很高兴再次见到你，指挥官。你的下一个任务高度机密，将把你带到中朝边境。肮脏的北美侵略者及其韩国盟友打垮了朝鲜人民军。去年夏天金日成几乎取得全胜，但他没有保护好后方，如你所知，资本主义势力在仁川和汉城的行动已彻底粉碎了朝鲜对釜山的进攻。',
 'We can''t allow this situation; the capitalist unification of Korea must not be completed.  A capitalist state in Korea would be like a gun aimed at the People''s Republic of China, and we know that the puny North American general McArthur has maintained some conversations with Chaing-Kai-Shek about a possible continuation of the war against us.|我们不能允许这种局面，资本主义统一朝鲜的图谋绝不能得逞。朝鲜出现一个资本主义国家，就像一支枪口对准中华人民共和国的枪，而且我们知道，那个微不足道的北美将军麦克阿瑟一直在同蒋介石商谈可能继续对我们开战的事。',
 'Welcome again commander.  We have escaped from Jingghanshan in our long march to the North.  Today the Dadu River lies in front of us, and your task is to cross that river.  The problem is, we have in front the city of Luding, which is in the hands of the local pro-KMT Warlord Liu Wenhui.  I see the chains bridge over the Dadu River is on fire, but our long march can''t be stopped!  Go ahead soldier!|欢迎回来，指挥官。我们在向北的长征中已撤离井冈山。今天大渡河横在我们面前，你的任务是渡过大渡河。问题是前方泸定城掌握在亲国民党的当地军阀刘文辉手中。我看到大渡河上的铁索桥正在燃烧，但我们的长征不能停下！前进吧，战士！',
 'Comrade Mao has established a "Soviet Commune'''' here in the Jinggangshan Mountains.  It is well protected and hidden from our enemies by a heavy wilderness and bamboo trees.  All the access points to our base are under continuous servalance and our Soviet GRU spies report that the Kuomingtan enemies and the Warlords are planning to eradicate us at once.  They are supported by German advisors who think the best way to eliminate us from here is the so-called strategy ''''ferocious walls''''.|毛泽东同志在井冈山建立了“苏维埃公社”。这里被茂密的荒野和竹林遮蔽，防护严密，敌人难以发现。通往我根据地的所有通路都处于持续监视之下，我们苏联格鲁乌的情报员报告，国民党敌人和军阀正打算一举消灭我们。他们有德国顾问支持，这些顾问认为把我们赶出这里的最好办法就是所谓的“铁壁”策略。',
 'Our Soviet advisors suggest that we let the enemy troops pass through the mountains and then annihilate them on a familiar battlefield.|我们的苏联顾问建议让敌军穿过山区，然后在熟悉的战场上歼灭他们。',
 'The entire blame for the encicrlement of 6th army is on the general of the 22nd Pz division.|第6集团军被围的全部责任都在第22装甲师师长的身上。',
 'We now expect the Russians to poor in troops in order to march on the Chir, be ready for an attack from the east.|现在我们预计俄军会大量涌入，以便向奇尔河推进，要做好从东面遭到进攻的准备。',
 'We have a disastrous situation on our hands and where it not for you, sixth army would be all but finished now. East of Serafimovitch two Russian corps have broken through the Romanian lines, destroyed three Roumanian divisions, and routed three divisions of Sixth Army. South of Stalingrad the Roumanian fourth army has been annihalated. Though it still holds Kalach, sixth army is surrounded in a perimeter west of Stalingrad, and in a disastrous position.|我们手上的局势极为糟糕，若不是你，第6集团军现在几乎已经完了。在谢拉菲莫维奇以东，俄军两个军突破了罗马尼亚军队的防线，击溃了罗马尼亚3个师，并打垮了第6集团军的3个师。在斯大林格勒以南，罗马尼亚第4集团军已被歼灭。第6集团军虽然仍守着卡拉奇，却已在斯大林格勒以西被围在一个环形阵地里，处境极为糟糕。',
 'Instead of sending your divisions to Paulus we have decided to send you to this part of the Roumanian sector. Though the Roumanians are tough fighters they do not have any Anti tank capability. You are to secure their positions by integrating your panzerjaeger regiments into their defensive positions.|我们没有把你的师派给保卢斯，而是决定把你派到罗马尼亚地段的这一部分。罗马尼亚人虽然能打硬仗，却完全没有反坦克能力。你要把你的反坦克歼击团编入他们的防御阵地，以稳固其防线。',
 'We have however indications from General Richthofen that large formations, probably the Soviet first guard corps are on their way east to your sector. So, be on your guard against an attack from the east as well as a renewed attack from the north !|不过，我们从里希特霍芬将军那里得到迹象表明，庞大的兵团——很可能是苏联近卫第1军——正东进开往你的地段。所以，既要提防东面的进攻，也要提防北面再次发起的进攻！',
 'I am glad to hear that you have reshuffeled your positions in order to close the gap in our front. It now runs along an imaginairy line from Serafimovitch to Nizhne Chirskaya and so far, it looks alright with remains of the 1st Roumanian Pz supporting Axis troops holding the southern part. |我很高兴听说你重新调整了阵地，以封闭我们正面的缺口。这条战线现在沿谢拉菲莫维奇到下奇尔斯卡亚之间的一条假想线展开，到目前为止情况尚可，罗马尼亚第1装甲师的残部正支援轴心国部队守住了南段。',
 'General, deploy your forces along the front lines we have reached in the past months. Be careful, the lines are not safe; althought we are near to Jilin, Changchun and Siping, the KMT forces still keep a strong attack axis near to our base at Linjiang. The mission will be a complete success if you can besiege Changchun and Jilin, and stop the KMT''s assault on Linjiang, GRU spies reports our enemies will also try to recapture the section of the Beijing-Changchun railroad, which is also now our main supply line, protect it at any costs!|将军，把你麾下的部队沿我们近几个月推进到的战线展开。要小心，战线并不安全；虽然我们已逼近吉林、长春和四平，国民党军队仍在靠近我们临江根据地处保持着一个强大的进攻轴线。如果你能围困长春和吉林，并阻止国民党对临江的进攻，这次任务就将取得完全成功。格鲁乌情报员报告，敌人还将试图夺回北平至长春铁路的路段，那也是我们目前的主要补给线，不惜一切代价保护它！',
 'Your first assignment as PLA''s commander will be in the Jilin province, our base there is placed at Linjiang. The situation in Manchuria is complex. We need Manchuria for some reasons, first, it''s border is close with the USSR and the support we are receiving from the Soviets, and second, Manchuria is the most industrialised area in the whole China, we need the resources from here, and we need to avoid the profits the Kuomingtang can get from here.|你作为解放军指挥员的第一项任务将在吉林省，我们在那里的根据地位于临江。满洲的局势很复杂。出于若干原因，我们需要满洲：第一，它的边界靠近苏联，便于接受苏联给我们的支援；第二，满洲是全中国工业化程度最高的地区，我们需要这里的资源，也必须避免国民党从这里获得好处。',
 'Congratulations on your promotion to commander of our reciently created People''s Liberation Army!. Your actions were enough to support your upgrade decided in the ChCP council... Mao Zedong it''s also pleased with you as PLA''s general.|祝贺你晋升为我们新近组建的中国人民解放军指挥员！你的战绩足以支持中共中央委员会作出提升你的决定……毛泽东也很满意你担任解放军将领。',
 'It is with great sadness that I must tell you the commander of the 22 nd Pz has died|我怀着极大的悲痛必须告诉你，第22装甲师师长已经阵亡',
 'The KMT troops are badly wounded.  Our victories at Changchun and Siping have decimated their men, commander, and you must put an end to the nationalist resistance in Manchuria.  Your mission is to secure the communications between our base at Siping and our groups in the South, near to Shenyang.  Then you must take Shenyang.  It is the historical Manchurian capital and is both an important industrial and political center.  The capture of Shenyang will open the way to Beijing and Nanjing.|国民党军队已遭重创。我们在长春和四平的胜利大量歼灭了他们的兵力，指挥官，你必须终结国民党在满洲的抵抗。你的任务是保障我们四平根据地与沈阳附近南方各部队之间的交通线，然后必须攻取沈阳。它是历史上的满洲首府，既是重要的工业中心，也是重要的政治中心。夺取沈阳将打开通往北平与南京的道路。',
 'I don''t think the snow and the bad weather conditions of the Manchurian Winter will be a major problem for you.|我认为满洲冬季的冰雪和恶劣天气不会给你造成大麻烦。',
 'It won''t be easy, the nationalists still have good units with good equipment, but we count on your elite units to deal with the Kuomingtan troops. The planned Summer Offensive must be victorious.|这不会容易，国民党仍拥有装备精良的部队，但我们指望你的精锐部队来对付国民党军。计划中的夏季攻势必须取得胜利。',
 'Orders from the central ChCP comitte: it''s time to capture Changchun, Siping, and Jilin to complete the conquest of Manchuria. The success on this offensive is extremely important, because it would allow us to undertake further penetrations on to Beijing and Nanjing in the next months.|中共中央委员会的命令：现在是攻取长春、四平和吉林，完成征服满洲的时候了。这次攻势的成功极其重要，因为它将使我们能够在接下来的几个月里进一步向北平与南京挺进。',
 'Your mission is to reach the port of Hungnam while destroying all enemy forces along your way.  You must stop any UN evacuation as soon as possible.  A successful evacuation will be a victory for them.  The 2nd, 6th and 10th North Korean divisions (the 2nd Korean People''s Army) will be under your direct command and the 20th PLA will arrive from the South as reinforcements.|你的任务是抵达兴南港，并沿途歼灭所有敌军。你必须尽快阻止联合国军的任何撤退。他们若撤退成功，就是他们的胜利。朝鲜人民军第2、第6和第10师（朝鲜人民军第2军团）将归你直接指挥，解放军第20军将从南面赶来增援。',
 'Again, your smashing attack has left the enemy forces on the ground isolated.  This is the situation at Hungnam.  The UN forces are surrounded from the North and South by us while the North Korean units will attack from the East.  However, the Hungnam port continues to be their main lifeline, supported by their overwhelming naval power.|你的猛烈进攻又一次使地面上的敌军陷入孤立。兴南的情况就是这样。联合国军南北两面被我们包围，朝鲜部队将从东面发起攻击。然而，兴南港仍是他们的主要生命线，并有他们压倒性的海军力量支援。',
 'Some UN forces have escaped from Hungnam, but at least we can now continue with our advance towards Seoul.|一部分联合国军已从兴南逃脱，但至少我们现在可以继续向汉城推进了。',
 'Most of the UN forces have escaped and you have suffered heavy causalities.  You, commander, will meet a People''s Court to determine if you are a capitalist sympathizer.|大部分联合国军已经逃脱，而你伤亡惨重。指挥官，你将面对人民法庭，以判定你是否是资本家的同情者。',
 'The lightning advances of December and early January provide us with the opportunity to easily retake Seoul for the North Koreans.  However, the situation is becoming dangerous.  Our supply lines to China are long and are constantly being bombed and strafed by the UN air force.  Because of this they are preparing a counterattack to again liberate Seoul.  Our Korean spies have told us that a great number of troops are concentrating South of Suwon, including modern tanks and heavy artillery.|12月和1月初的闪电推进为我们提供了为朝鲜人民轻松夺回汉城的机会。然而局势正变得危险。我们通往中国的补给线太长，且不断遭到联合国军空军的轰炸与扫射。因此，他们正在准备一次反攻，以再次解放汉城。我们的朝鲜情报员告诉我们，大量部队正在水原以南集结，其中包括现代坦克和重型火炮。',
 'Seoul, beyond the 38th Paralell, near to the former DMZ.|汉城，三八线以南，靠近旧军事分界线。',
 'You have crushed the UN forces with a smashing victory!  Now, we can continue with our advance towards Seoul.|你以一场雷霆大胜粉碎了联合国军！现在，我们可以继续向汉城推进了。',
 'We have stopped the offensive, but our casualities have been too high.  You have permission to retreat your armies behind the Han river to avoid future losses.|我们挡住了这次攻势，但我方伤亡太高。准许你把部队撤到汉江以北，以避免日后的损失。',
 'Be careful, our troops are nearly exhausted due to the quick advances in the past months. Your mission is to protect Seoul at all costs and if possible defeat the capitalist advance.|要小心，由于近几个月快速推进，我军已几近精疲力竭。你的任务是不惜一切代价保卫汉城，并在可能的情况下粉碎资本主义势力的进攻。',
 'A chain of unfortunate incidents with the Soviets along the Chinese - Soviet border has opened the way for the outbreak of full scale military operations.  As you know, the relationship with our former Soviet allies has badly deteriorated.  Moscow doesn''t like our own interpretation of Marxism and wants to take us back to the ''''correct'''' communist system.  To punish us, they have launched an invasion across the Amur River, the natural border between the PRC and the USSR.  They have captured a many square kilometers of Chinese territory, including some villages.|中苏边境上一连串不幸事件，为全面军事行动的爆发开了路。如你所知，我们与前苏联盟友的关系已严重恶化。莫斯科不喜欢我们对马克思主义的自家解释，想让我们回到“正确”的共产主义体制上去。为了惩罚我们，他们越过黑龙江——中华人民共和国与苏联之间的天然边界——发动了入侵。他们已占领大片中国领土，包括一些村庄。',
 'You are the commander of the best units in the whole PLA, and your mission is to counter-strike the Soviet invaders.  If we want to continue with our own interpretation of the Marxism, we must defeat the Soviets.  Also Mao would be most pleased, if your men capture the important city of Khabarovsk.  He says that these territories are historically Chinese and no soviets must remain on Chinese lands! |你是整个解放军中最精锐部队的指挥员，你的任务是对苏联入侵者实施反击。如果我们想继续坚持自己对马克思主义的解释，就必须打败苏联人。另外，如果你的人攻占重要城市哈巴罗夫斯克，毛泽东会非常高兴。他说这些领土历史上属于中国，中国土地上不能留下任何苏联人！',
 'Your quick advance has created a salient in the enemy lines, like the one at the Chosin Reservoir.  This sector is protected by a North American division.  Your task is to make a surprise attack from two different directions and destroy the entire enemy division.  Be careful, our spies report that it''s a crack division and they have air support from an improvised airstrip near the reservoir.  Air reinforcements are on the way.|你的快速推进在敌人战线上形成了一个突出部，长津湖这里就是如此。该地段由一个北美师防守。你的任务是从两个不同方向发起突袭，全歼敌师。要小心，我们的情报员报告说那是一支精锐师，而且他们有水库附近一座临时机场提供的空中支援。空中增援正在赶来。',
 'I was completely wrong about you and maybe also with your friend Zhou, hmmm or maybe not.  I think China deserves a return to the true Revolution to avoid the capitalist deformation that you have suffered.|我完全看错了你，也许对你的朋友周也一样，嗯，也许并不是。我认为中国应当回归真正的革命，以免遭受你已染上的那种资本主义蜕变。',
 'AH!  You dirty rebel and traitor!.  You, the former hero of the People''s Republic of China are now a coward capitalist traitor.  Your execution will be soon be celebrated in Tiananmen Square.|啊！你这个肮脏的叛乱分子和叛徒！你，昔日中华人民共和国的英雄，如今成了怯懦的资产阶级叛徒。你的处决很快将在天安门广场上被庆祝。',
 'Private Tovarich!  Nice to see you again.  It has been a while since our last meeting at Khabarovsk.  It was a shame to lose the battle against you, but now we can re-negotiate the conditions of the peace treaty.  This is Top Secret and I hope you have told no one of our plans.  As our men from the KGB have told you, we are ready to support you, if you finally decide to undertake a coup against Mao Zedong and his reformed communism.  It is literally destroying China.  We need to take China back to the right and true communist way.  We think you and your so-called ''''Gang of Four'''' are the perfect team to take down the Maoist system and that destructive plan named ''''Great Leap Forward''''.  That woman of your gang, ''''Madame Mao'''' can be very useful in the near future, when you will need to destroy the political image of Mao.|列兵同志！很高兴再次见到你。距离我们上次在哈巴罗夫斯克会面已经有一段时间了。败给你真是遗憾，不过现在我们可以重新商谈和约的条件了。这是最高机密，我希望你没有把我们的计划告诉任何人。正如我们克格勃的人告诉你的，如果你最终决定对毛泽东及其改革后的共产主义发动政变，我们随时准备支持你。那套东西正在实实在在地摧毁中国。我们需要让中国回到正确而真正的共产主义道路上去。我们认为你和你所谓的“四人帮”是推翻毛主义体制以及那个名为“大跃进”的破坏性计划的完美组合。你们团伙里的那个女人，“毛夫人”，在不久的将来会非常有用，那时你需要摧毁毛泽东的政治形象。',
 'The last stand will be Beijing, this won''t be easy, as you know, the best PLA units are deployed there.  The price maybe high, but it deserves a try.  You can become the new premier of the People''s Republic of China!|最后一道防线将是北京，这不会容易，如你所知，解放军最精锐的部队都部署在那里。代价可能很高，但值得一试。你可以成为中华人民共和国的新总理！',
 'This is the plan we suggest; in the past month the units under your direct management have been deployed on the coast of the Sea of China in preparation for the Coup.   We are ready to support you by sea.  The Chinese navy will remain loyal to Mao, but it is not powerful enough to deal with a minor Soviet submarine unit.  After we secure the entire coast by taking Tanggu, you must launch the counterattack against the government loyalist units which surely will be sent to defeat our plans.  Take the Tanggu airfield as soon as possible as this will allow us to send you reinforcements by air.  Our planes will be painted with the PRC symbols.  You must avoid the Americans as we don''t need any problems with them now.  The incident should be only between Chinese forces.|这是我们建议的计划：过去一个月里，你直接掌管的部队已部署在中国海沿岸，为政变做准备。我们准备从海上支援你。中国海军仍将效忠毛泽东，但它不够强大，对付不了一支小规模的苏联潜艇部队。在我们攻占塘沽、控制整条海岸线之后，你必须对那些必然会被派来挫败我们计划的政府效忠派部队发起反击。尽快夺取塘沽机场，这样我们就能向你们空运增援。我们的飞机会涂上中华人民共和国的标志。你必须避开美国人，因为我们现在不需要与他们发生任何麻烦。这次事件应当只在中国军队之间进行。',
 'Brave soldiers under my command!  The so-called ''''united front'''' with the Kuomingtan is over.  Today we will join the revolution against the ancient oppressors of the Chinese people and against the likes of Chiang-Kai-Shek.  Some of our comrades in other army units will also join us in our glorious uprising against the enemies of the people.  They are just now coming here to help us in the assault on the old city of Nanchang!  The end of the oppression, the capitalism, and the humiliations begins here on the West bank of the Gan River!  We are surrounded by the local warlords KMT troops, but our comrades will attack them from different directions, and the victory will be ours!|我麾下勇敢的士兵们！与国民党所谓的“统一战线”已经结束。今天我们将投身革命，反抗中国人民古老的压迫者，反抗蒋介石之流。我们在其他部队的一些同志也将加入我们这场反对人民之敌的光荣起义。他们此刻正赶来此地，协助我们攻打南昌老城！压迫、资本主义与屈辱的终结，就从赣江西岸这里开始！我们被当地军阀的国民党军队包围，但我们的同志将从不同方向攻击他们，胜利必将属于我们！',
 'It''s time to go back to Seoul.  We have deployed a large number of PLA and KPA units Northwards toward Seoul and with your armies nothing will stop us in our drive.  The South Korean capital must be in our hands again.|是时候回到汉城了。我们已把大量解放军和朝鲜人民军部队向北调往汉城方向，有你的部队在，我们的进军将无可阻挡。韩国首都必须重新回到我们手中。',
 'The UN forces have massed their units to protect their silly so-called ''''No-Named line''''.  Anyway, this situation fits perfectly with our People''s War doctrine.  Launch your armies and over run the dirty capitalist''s invaders on your way to recapture Seoul.|联合国军集结部队来保护他们那条可笑地称作“无名防线”的阵地。无论如何，这种局面完全符合我们人民战争的学说。发动你的部队，在夺回汉城的途中碾碎这些肮脏的资本主义侵略者。',
 'Just like last year, the UN forces are again encircled on the ''''Pusan Perimeter''''.  Now, with the bulk of the North Korean forces are guarding the rear, we can assault the enemy positions without the fear of an assault on our back like last years landings at Inch''on.|就像去年一样，联合国军又一次被围困在“釜山环形防御圈”里。现在，由于朝鲜人民军主力正在守卫后方，我们可以攻击敌军阵地，而不必担心像去年仁川登陆那样背后挨一刀。',
 'You have one mission; destroy the remnants of the capitalist forces.  Otherwise, they will receive more reinforcements and support from their stronghold at Pusan.  Quick drive them into the sea and Korea will become the unified Korean People''s Republic.|你只有一个任务：消灭资本主义势力的残部。否则，他们会从釜山这个据点获得更多增援和支持。赶快把他们赶下海，朝鲜就将成为统一的朝鲜人民共和国。',
 'I hope you had enough rest from your participation on the Korean War.  As one of the heroes of the PRC the High Command of the PLA has a new mission for you.  The new North American government has retired the fleet that was guarding the Taiwan Strait.  This is the opportunity we have been waiting for; the assault on the rebel province of Taiwan.  You must end the existence of the KMT and its leader, Chiang-Kai-Shek.|希望你从朝鲜战争的征战中已经休息够了。作为中华人民共和国的英雄之一，解放军最高统帅部给你一项新任务。北美新政府已撤走了守卫台湾海峡的舰队。这是我们一直等待的机会：进攻叛乱省份台湾。你必须终结国民党及其领导人蒋介石的存在。',
 'Embark your units in Tianjing and reach the Taiwanese coast as soon as possible.  Beijing is sure the UN will take part in operations like in Korea, this time supporting the KMT in Taiwan.  Your highest priority is the conquest of Taipei.  With this city we will complete the unification of all the Chinese territories.|让你的部队在天津登船，尽快抵达台湾海岸。北京确信联合国会像在朝鲜那样参与作战，这一次是支持台湾的国民党。你的最高优先目标是攻取台北。拿下这座城市，我们就将完成全中国领土的统一。'
)
$MAP=@{}
foreach($p in $PH){ $k,$v=$p -split '\|',2; $MAP[$k.TrimEnd()]=$v.TrimEnd() }
"phrases: $($MAP.Count)"

# ---------------------------------------------------------------- glossary
$G=@(
 'People''s Liberation Army Air Force|人民解放军空军','People''s Liberation Army|人民解放军','People''s Republic of Korea|朝鲜人民共和国',
 'People''s Republic of China|中华人民共和国','Republic of Korea|大韩民国','Korean People''s Republic|朝鲜人民共和国',
 'Korean People''s Army|朝鲜人民军','Chinese Communist Party|中国共产党','Communist Party|共产党',
 'ChCP|中共中央','PLA|解放军','KPA|朝鲜人民军','KMT|国民党','Kuomingtan|国民党','Kuomingtang|国民党',
 'Manchukuo|满洲国','Manchuria|满洲','Manchurian|满洲','Nationalist China|国民政府','Communist China|中国共产党',
 'Warlord China|军阀势力','Nanjing China|南京国民政府','Mengjiang|蒙疆','Fengtian clique|奉系',
 'Soviet Union|苏联','the Soviets|苏联','Soviets|苏联','Soviet|苏联','Russian|俄军','Russians|俄军',
 'North Americans|北美人','North American|北美','Americans|美国人','Americans|美军',
 'United Nations|联合国','UN forces|联合国军','UN|联合国','United States|美国','US|美国',
 'Japanese Empire|日本帝国','Japanese|日军','Japanese|日本的','Japan|日本','Germans|德军','German|德国',
 'Roumanians|罗马尼亚人','Roumanian|罗马尼亚','Romanian|罗马尼亚','Romanians|罗马尼亚人',
 'Turks|土耳其人','Turkish|土耳其','British|英军','Chiang Kai Shek|蒋介石','Chiang-Kai-Shek|蒋介石',
 'Chaing-Kai-Shek|蒋介石','Kim-Il-Sung|金日成','Mao Zedong|毛泽东','Madame Mao|毛夫人','Mao|毛泽东',
 'McArthur|麦克阿瑟','General Richthofen|里希特霍芬将军','Paulus|保卢斯','George Marshall|乔治·马歇尔',
 'Liu Wenhui|刘文辉','Zhu De|朱德','Lin Biao|林彪','Otto Braun|奥托·布劳恩','Gang of Four|四人帮',
 'Great Leap Forward|大跃进','Long March|长征','People''s War|人民战争','Pusan Perimeter|釜山环形防御圈',
 'No-Named line|无名防线','communist|共产主义','capitalist|资本主义','nationalist|国民党','nationalists|国民党',
 'Yalu River|鸭绿江','Amur River|黑龙江','Ussuri River|乌苏里江','Han river|汉江','Han River|汉江',
 'Dadu River|大渡河','Gan River|赣江','Song Hua River|松花江','Naktong River|洛东江','Imjin River|临津江',
 'Naktong-ni|洛东里','Chosin Reservoir|长津湖','Hwachon Reservoir|华川水库','Jinggangshan|井冈山',
 'Beijing|北平','Nanjing|南京','Tianjin|天津','Tanggu|塘沽','Taipei|台北','Pyongyang|平壤','Seoul|汉城',
 'Inch''on|仁川','Pusan|釜山','Hungnam|兴南','Hamhung|咸兴','Wonsan|元山','Khabarovsk|哈巴罗夫斯克',
 'Changchun|长春','Siping|四平','Shenyang|沈阳','Mukden|奉天','Jilin|吉林','Linjiang|临江','Liaoning|辽宁',
 'Stalingrad|斯大林格勒','Chir|奇尔河','Don River|顿河','Kalach|卡拉奇',
 'prestige|声望','initiative|先手','entrenchment|工事','supply|补给','reinforcements|增援','objective|目标',
 'Warlord|军阀','Warlords|军阀','Militia|民兵','Guerrilla|游击队','garrison|驻军','Garrison|驻军',
 'Regiment|团','Division|师','Corps|军','Column|纵队','Legion|军团','Brigade|旅','Battalion|营',
 'Headquarters|司令部','Commando|突击队','Airfield|机场','Air Strip|简易机场','Port|港口',
 'coal mines|煤矿','Coal Mines|煤矿','Railroad|铁路','destroyed|已被摧毁','DESTROYED|已被摧毁',
 'Victory|胜利','Defeat|失败','Defeat!|失败！','SNOW|雪地','LAKE|湖','Mountain Pass|山口','Dense Forest|密林',
 'Airfield|机场','Evacuation Point|撤离点','Radar Installation|雷达站','Bridging|架桥','Regular10|正规军10',
 'Luftwaffe|德国空军','US Navy|美国海军','Task Force|特遣队','Field Works|野战工事'
)
foreach($g in $G){ $k,$v=$g -split '\|',2; if(-not $MAP.ContainsKey($k)){ $MAP[$k]=$v } }
"glossary: $($MAP.Count)"

# ---------------------------------------------------------------- translit
$SYL=@{}
function AddSyl($k,$vals){ foreach($v in $vals){ if(-not $SYL.ContainsKey($k)){ $SYL[$k]=$v } } }
AddSyl 'a','阿'; AddSyl 'e','埃'; AddSyl 'i','伊'; AddSyl 'o','奥'; AddSyl 'u','乌'
AddSyl 'ai','艾'; AddSyl 'ay','艾'; AddSyl 'ei','埃'; AddSyl 'ey','埃'; AddSyl 'oi','奥伊'; AddSyl 'oy','奥伊'
AddSyl 'au','奥'; AddSyl 'aw','奥'; AddSyl 'ou','欧'; AddSyl 'ow','欧'
AddSyl 'ia','亚'; AddSyl 'ie','耶'; AddSyl 'io','约'; AddSyl 'iu','尤'; AddSyl 'ya','亚'; AddSyl 'ye','耶'; AddSyl 'yo','约'; AddSyl 'yu','尤'
AddSyl 'ua','瓦'; AddSyl 'ue','韦'; AddSyl 'uo','沃'; AddSyl 'ui','维'; AddSyl 'wa','瓦'; AddSyl 'we','韦'; AddSyl 'wo','沃'; AddSyl 'wi','维'
$ONS=@{ 'b'='布';'c'='克';'ch'='奇';'d'='德';'dh'='德';'f'='夫';'g'='格';'gh'='格';'h'='赫';'j'='杰';'k'='克';'kh'='赫';
 'l'='尔';'m'='姆';'n'='恩';'p'='普';'ph'='夫';'q'='克';'r'='尔';'s'='斯';'sh'='什';'t'='特';'th'='特';'ts'='茨';
 'v'='夫';'w'='沃';'x'='克';'y'='伊';'z'='兹';'zh'='日' }
$COD=@{ 'n'='恩';'m'='姆';'ng'='昂';'r'='尔';'l'='尔';'s'='斯';'t'='特';'k'='克';'p'='普';'d'='德' }
function translit([string]$w){
  $w=$w.ToLower()
  $w=$w -replace "[^a-z]",''
  if($w.Length -eq 0){ return '' }
  $w=$w -replace 'ck','k' -replace 'ph','f' -replace 'sh','S' -replace 'ch','C' -replace 'th','T' -replace 'zh','Z'
  $w=$w -replace 'qu','kw' -replace 'x','ks' -replace 'q','k'
  # split into units: vowel groups / consonant runs
  $m=[regex]::Matches($w,'[aeiouy]+|[^aeiouy]+')
  $seg=@()
  foreach($x in $m){ $seg+=$x.Value }
  $res=''
  $first=$true
  for($i=0;$i -lt $seg.Count;$i++){
    $cur=$seg[$i]
    if($cur -match '^[aeiouy]'){
      $v=$cur
      # merge y-glide with following short vowel
      if($v.Length -ge 2 -and ($v -match '^[aeiou]y[a-z]?$' -or $v -match '^y[aeiou]$')){ }
      elseif($v -match '^([aeiou])y$'){ $v=$Matches[1] }
      $lookup=$v
      if(-not $SYL.ContainsKey($lookup)){
        while($lookup.Length -gt 1 -and -not $SYL.ContainsKey($lookup)){ $lookup=$lookup.Substring(0,$lookup.Length-1) }
        if($lookup.Length -eq 0){ $lookup=$v.Substring(0,1) }
      }
      $res += $SYL[$lookup]
      $rest = $v.Substring($lookup.Length)
      if($rest.Length -gt 0){ $res += (translit $rest) }
      if($i+1 -lt $seg.Count -and $seg[$i+1] -match '^[^aeiouy]+$' -and ($i+2 -lt $seg.Count)){
        $cl=$seg[$i+1]
        # coda candidates
        $cand=''
        if($cl.Length -ge 2 -and $cl.EndsWith('ng')){ $cand='ng' }
        elseif('nmrlstkpd'.Contains($cl.Substring($cl.Length-1)) -and $cl.Length -ge 2){ $cand=$cl.Substring($cl.Length-1) }
        if($cand -ne '' -and $COD.ContainsKey($cand)){
          $res += $COD[$cand]
          $seg[$i+1] = $cl.Substring(0,$cl.Length-$cand.Length)
        }
      }
    } else {
      # consonant run
      if($i+1 -lt $seg.Count -and $seg[$i+1] -match '^[aeiouy]'){
        $cl=$cur
        if($cl.Length -eq 0){ continue }
        $cc=$cl
        if($cc.Length -ge 2 -and $ONS.ContainsKey($cc)){ $res += $ONS[$cc] }
        elseif($cc.Length -ge 3 -and $ONS.ContainsKey($cc.Substring(0,2)) -and $ONS.ContainsKey($cc.Substring(2))){ $res += $ONS[$cc.Substring(0,2)] + $ONS[$cc.Substring(2)] }
        else {
          if($ONS.ContainsKey($cc.Substring(0,1))){ $res += $ONS[$cc.Substring(0,1)] }
          if($cc.Length -ge 2 -and $ONS.ContainsKey($cc.Substring(1,1))){ $res += $ONS[$cc.Substring(1,1)] }
        }
      }
    }
    $first=$false
  }
  # map internal markers back
  $res = $res -replace 'S','什' -replace 'C','奇' -replace 'T','特' -replace 'Z','日'
  return $res
}

# ---------------------------------------------------------------- token rules
