# HARVEST REPORT — Jesse Lauriston Livermore (1877-11-26 – 1940-11-28)

抓取日期 2026-08-01。表内每一行都来自**实际发生的 HTTP 请求**；未抓到的一律记 failed，无一条凭印象补写。

## 一、六个数字

| | 指标 | 数 |
|---|---|---|
| 1 | 实际抓取成功的文件数 | **542**（541 份报纸整版 OCR + 1 份本人署名专著） |
| 2 | 其中他本人署名（byline 含其名） | **1** —— 仅 1940 年《How to Trade in Stocks》一种 |
| 3 | 含明确归给他的引号直引的文件 / 直引句总条数 | **14 份 / 28 条**（逐条读上下文人工核过） |
| 4 | 纯第三方叙述（无本人直引） | **527** |
| 5 | Lefèvre 及其衍生（单列，不计入可用） | **3** |
| 6 | 真失败（网络/HTTP 非 200） | **4**；另有 **53** 份下载成功但整版 OCR 里查无 'Livermore'（检索索引与 OCR 不一致），已按无效剔除、未存盘 |

> 第 3 行是**人工判读后**的数字。自动检测器初筛出的候选里，大量是同版面其他报道的引语、或说话人其实是 **Livermore 夫人／他的律师／国会议员**——这些已全部剔除，剔除理由见第四节。

## 二、端点实况（与任务书给的路径不一致，务必注意）

| 端点 | 结果 |
|---|---|
| `chroniclingamerica.loc.gov/search/pages/results/?format=json` | **失效**：301 跳 `www.loc.gov` 后 404 |
| `chroniclingamerica.loc.gov/lccn/.../ocr.txt` | **失效**：301 后 403，该路径已不存在 |
| `www.loc.gov/collections/chronicling-america/?q=…&fo=json` | **可用**，但对 curl/WebFetch 一律 403（Cloudflare 挑战），只有真实浏览器会话能取 |
| `tile.loc.gov/storage-services/service/ndnp/<awardee>/<batch>/data/<lccn>/<reel>/<dateed>/<seq>.xml` | **可用且 curl 可直连** —— 全文实际来源（ALTO XML，解析 `String@CONTENT`） |
| HathiTrust / Stanford Copyright Renewal DB / NYS Historic Newspapers / CDNC | **全部 403 Cloudflare**，未取到任何数据 |
| archive.org、gutendex/Project Gutenberg | 可用 |

检索词与命中量（新端点报告的 total）：`"jesse l. livermore"` 450、`"jesse livermore"` 613、`"boy plunger"` 327，另加 6 组针对性检索（其本人声明／证词／还债／访谈）。

## 三、本人直引清单（人工核实，逐字）


**1940-11-29 · evening star (washington, d.c.) 1854-1972** — `jl_1940_eveningstar_009.txt`  
https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603077/1940112901/0414.xml

1. “I am a failure”
2. “I am tired of fighting. I can't go on.”
3. “took speculation out of speculating”
4. “The only way I know for any one to succeed in stocks ... is to investigate before investing, to look before he leaps; to stick to the fundamentals.”
5. “But, I can't remember back 20 years or so.”

**1923-12-21 · the washington times (washington [d.c.]) 1902-1939** — `jl_1923_thewashingtontim_122.txt`  
https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/0022225405A/1923122101/0780.xml

6. “I was employed to steady the market.”
7. “My idea was to make a stable market, and as the company grew to increase the value of the stock in the future. I would not allow my name to be used unless I had the privilege of buying back and creating a steady market so that the public could sell.”
8. “Of course, in buying the stock back at higher prices, there was a loss and I realized a profit of only $9,916 on the total transaction.”

**1932-10-05 · the indianapolis times (indianapolis [ind.]) 1922-1965** — `jl_1932_theindianapolist_052.txt`  
https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_huxley_ver01/data/sn82015313/0038334945A/1932100501/0390.xml

9. “Gentlemen, I have paid them.”
10. “All of them. A hundred cents on the dollar. I have paid for my mistakes, too, and one of them cost me $2,000,000.”

**1934-06-28 · the washington times (washington [d.c.]) 1902-1939** — `jl_1934_thewashingtontim_034.txt`  
https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/00205696623/1934062801/0760.xml

11. “I intend to get right back to work, to restore my fortune and pay my creditors as I have done in the past.”

**1934-04-18 · san antonio light (san antonio, tex.) 1911-1993** — `jl_1934_sanantoniolight_086.txt`  
https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994320/1934041801/0588.xml

12. “I've owed that much many times and I've always paid it off.”

**1923-11-13 · el dorado daily news (el dorado, ark.) 19??-1974** — `jl_1923_eldoradodailynew_080.txt`  
https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_hauerite_ver01/data/sn88084083/00516990648/1923111301/1064.xml

13. “During the past few years the people of our country have become accustomed to living on a higher standard than heretofore, and they are not going to be satisfied to live any other way in the future. The money they spend must necessarily mean a larger purchasing power and that purchasing power is bound to keep business [good].”

**1923-02-05 · the washington times (washington [d.c.]) 1902-1939** — `jl_1923_thewashingtontim_016.txt`  
https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/00222253949/1923020501/0471.xml

14. “I do not believe that the railroad problem will be effectively solved until we succeed in bringing our present scattered systems [together] ...”
15. “[chart makers and "dopesters"] are wasting their time in making small money where they should be piling up millions by the use of their own dope.”

**1910-08-20 · the detroit times (detroit, mich.) 1903-1920** — `jl_1910_thedetroittimes_023.txt`  
https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_gulliver_ver01/data/sn83016689/00279551680/1910082001/0002.xml

16. “I don't expect I will ever need it, but I want to make sure that if I lose every other dollar I've got, I will still have the means on which to live.”

**1908-05-15 · the news-democrat (providence, r.i.) 1906-1909** — `jl_1908_thenewsdemocrat_282.txt`  
https://tile.loc.gov/storage-services/service/ndnp/rp/batch_rp_crawlingclaw_ver03/data/sn91070633/0051415384A/1908051501/0959.xml

17. “I thought the traders would believe that.”
18. “No, I simply sold out all my July cotton. I began to sell on Wednesday and completed my sales this morning. It was a good market to sell on at the opening, so I let everyone who wanted cotton badly have it. Corners are all very well in their way, but I never will try to carry out a corner in cotton. I have completed my July deal and will now watch.”

**1922-10-16 · the indianapolis times (indianapolis [ind.]) 1922-1965** — `jl_1922_theindianapolist_247.txt`  
https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348675/1922101601/0656.xml

19. “I am not a gambler. I am a speculative investor.”

**1923-11-13 · americus times-recorder (americus, ga.;[americus, ga.?]** — `jl_1923_americustimesrec_390.txt`  
https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_eridanus_ver02/data/sn89053204/00393343655/1923111301/0388.xml

20. “During the past few years the people of our country have become accustomed to living on a higher standard than heretofore, and they are not going to be satisfied to live any other way in the future. ... (同一份通稿，另见 El Dorado Daily News 1923-11-13)”

**1924-02-22 · casper daily tribune (casper, wyo.) 1916-1931** — `jl_1924_casperdailytribu_505.txt`  
https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150473/1924022201/0317.xml

21. “It was bad judgment.”
22. “There I was on a falling market, collecting bales and bales of the stuff.”

**1940-09-22 · evening star (washington, d.c.) 1854-1972** — `jl_1940_eveningstar_431.txt`  
https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603016/1940092201/0691.xml

23. “If earnings of various companies are increased from 100 to 200 per cent, what does it matter if 50 per cent of that increase does not have to be paid out in increased taxes?”
24. “If any one thinks Germany is going to be able to subdue England in a comparatively short space of time, he should not own any stocks at all.”
25. “I have never seen anybody make profits in the stock market who allows himself to be swayed by fear. Only those who have courage and common sense judgment make money in the market.”
26. “For those who think that England is going to stay in this war until Germany admits defeat, I believe the market holds opportunities the same as existed one year after the World War had been in progress.”

**1940-11-29 · the waterbury democrat (waterbury, conn.) 1917-1946** — `jl_1940_thewaterburydemo_409.txt`  
https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_hepburn_ver01/data/sn82014085/00393347648/1940112901/0452.xml

27. “I am not worthy of your love. I am a failure.”
28. “[遗书另二片段] tired of fighting / not go on any longer”

## 四、被剔除的误判（自动检测器初筛出但说话人不是他）

- `jl_1922_thethermopolisin_010.txt` — speaker is Rep. Mondell in the Congressional Record, not Livermore
- `jl_1934_eveningstar_056.txt` — speaker is Livermore's lawyer Samuel F. Gillman
- `jl_1933_theindianapolist_064.txt` — speaker is Mrs. Livermore (wife)
- `jl_1933_thewashingtontim_134.txt` — speaker is Mrs. Livermore (wife)
- `jl_1925_thewashingtontim_054.txt` — speaker is Mrs. Livermore (wife)
- `jl_1934_sanantoniolight_086.txt` — one of three flagged quotes is his attorney; another is an unrelated shooting story on the same page
- `jl_1917_newyorktribune_135.txt` — court Q&A about 'J. L. L.' spoken by another witness
- `jl_1935_sanantoniolight_027.txt` — family/doctor dialogue in the Jesse Jr. shooting story
- `jl_1922_theindianapolist_247.txt` — 同版另一条引语说话人是 Barnes，不是 Livermore（已只保留 Livermore 那句）
- `jl_1924_thewashingtondai_491.txt` — 'All history proves that extravagance…' 说话人存疑，疑为议员评论，未采信
- `jl_1940_thewilmingtonmor_563.txt` — 命中的是同版伦敦战讯，与本人无关

## 五、明细表

| # | 文件名 | URL | 年份 | HTTP | 字节 | 类型 |
|---|---|---|---|---|---|---|
| 1 | `raw/jl_1940_HowToTradeInStocks_01.txt` | https://archive.org/details/how-to-trade-in-stocks-livermore-jesse-l-1940-duell-sloan-pearce-d-8d-4100576687 | 1940 | 200 | 126923 | **本人署名** |
| 2 | `raw/jl_1898_therepresentativ_258.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_ballet_ver01/data/sn90059591/00383346824/1898062901/0511.xml | 1898 | 200 | 1149543 | 纯第三方叙述 |
| 3 | `raw/jl_1898_eagleriverreview_245.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_arbutus_ver01/data/sn85040614/00514152652/1898091501/0247.xml | 1898 | 200 | 1225996 | 纯第三方叙述 |
| 4 | `raw/jl_1898_newyorktribune_312.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_universal_ver02/data/sn83030214/0017503691A/1898100701/0144.xml | 1898 | 200 | 1277174 | 纯第三方叙述 |
| 5 | `raw/jl_1898_lincolncountylea_223.txt` | https://tile.loc.gov/storage-services/service/ndnp/oru/batch_oru_flycatcher_ver01/data/sn85033162/00200298512/1898102101/0124.xml | 1898 | 200 | 789986 | 纯第三方叙述 |
| 6 | `raw/jl_1899_arizonarepublica_588.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_elk_ver01/data/sn84020558/0020219266A/1899042801/0745.xml | 1899 | 200 | 1140131 | 纯第三方叙述 |
| 7 | `raw/jl_1899_sanantoniodailyl_584.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_frisco_ver01/data/sn86090439/00517175109/1899052301/0186.xml | 1899 | 200 | 919933 | 纯第三方叙述 |
| 8 | `raw/jl_1899_sanantoniodailyl_582.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_frisco_ver01/data/sn86090439/00517175092/1899102601/0471.xml | 1899 | 200 | 757224 | 纯第三方叙述 |
| 9 | `raw/jl_1900_thejerseycitynew_221.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_illiciumverum_ver01/data/sn87068097/00383340317/1900010501/0019.xml | 1900 | 200 | 1223880 | 纯第三方叙述 |
| 10 | `raw/jl_1900_newyorktribune_281.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_iceland_ver02/data/sn83030214/00175040821/1900021401/0250.xml | 1900 | 200 | 1633471 | 纯第三方叙述 |
| 11 | `raw/jl_1900_gloucestercounty_349.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_furio_ver01/data/sn87068079/00332896519/1900071201/0322.xml | 1900 | 200 | 1715317 | 纯第三方叙述 |
| 12 | `raw/jl_1900_eveningtimesrepu_586.txt` | https://tile.loc.gov/storage-services/service/ndnp/iahi/batch_iahi_carson_ver01/data/sn85049554/00416159336/1900111001/0719.xml | 1900 | 200 | 797796 | 纯第三方叙述 |
| 13 | `raw/jl_1900_thewatchmanandso_229.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_danastjames_ver01/data/sn93067846/00294551177/1900122601/0487.xml | 1900 | 200 | 644526 | 纯第三方叙述 |
| 14 | `raw/jl_1901_thewomanstribune_581.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_europeanstarling_ver01/data/sn85038008/0054286624A/1901022301/0208.xml | 1901 | 200 | 508723 | 纯第三方叙述 |
| 15 | `raw/jl_1901_theminneapolisjo_301.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_richfield_ver01/data/sn83045366/00206533894/1901032601/0346.xml | 1901 | 200 | 1157478 | 纯第三方叙述 |
| 16 | `raw/jl_1901_thesundayglobe_294.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_echo_ver02/data/sn82016351/100493184/1901051901/0033.xml | 1901 | 200 | 1266652 | 纯第三方叙述 |
| 17 | `raw/jl_1901_ottumwasemiweekl_587.txt` | https://tile.loc.gov/storage-services/service/ndnp/iahi/batch_iahi_isbell_ver01/data/sn86061214/00415668697/1901070401/0096.xml | 1901 | 200 | 861731 | 纯第三方叙述 |
| 18 | `raw/jl_1901_thetopekastatejo_578.txt` | https://tile.loc.gov/storage-services/service/ndnp/khi/batch_khi_higuchi_ver01/data/sn82016014/00295871155/1901080101/0252.xml | 1901 | 200 | 1358903 | 纯第三方叙述 |
| 19 | `raw/jl_1901_conversecountyhe_249.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_firbolg_ver01/data/sn92067030/00516998878/1901080801/0010.xml | 1901 | 200 | 812782 | 纯第三方叙述 |
| 20 | `raw/jl_1902_theportlanddaily_309.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_jemptland_ver01/data/sn83016025/print/1902050701/0367.xml | 1902 | 200 | 933122 | 纯第三方叙述 |
| 21 | `raw/jl_1902_eveningstar_256.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_saluki_ver01/data/sn83045462/00280655624/1902111401/0340.xml | 1902 | 200 | 1148586 | 纯第三方叙述 |
| 22 | `raw/jl_1903_newyorktribune_276.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fiji_ver02/data/sn83030214/0017504209A/1903011301/0237.xml | 1903 | 200 | 1849549 | 纯第三方叙述 |
| 23 | `raw/jl_1903_newyorktribune_243.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fiji_ver02/data/sn83030214/00175042106/1903021101/0212.xml | 1903 | 200 | 2318274 | 纯第三方叙述 |
| 24 | `raw/jl_1903_thesanfranciscoc_253.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_etna_ver01/data/00100480414/1903061301/0202.xml | 1903 | 200 | 1095086 | 纯第三方叙述 |
| 25 | `raw/jl_1903_thesaintpaulglob_251.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_plymouth_ver01/data/sn90059523/00206539367/1903101401/0179.xml | 1903 | 200 | 1379196 | 纯第三方叙述 |
| 26 | `raw/jl_1904_theeveningworld_219.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_plato_ver01/data/sn83030193/175044450/1904012601/0292.xml | 1904 | 200 | 1322112 | 纯第三方叙述 |
| 27 | `raw/jl_1904_thehartfordrepub_496.txt` | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_gratefuldead_ver01/data/sn86069313/00175045570/1904062401/0222.xml | 1904 | 200 | 633101 | 纯第三方叙述 |
| 28 | `raw/jl_1904_thetopekastatejo_310.txt` | https://tile.loc.gov/storage-services/service/ndnp/khi/batch_khi_gygax_ver01/data/sn82016014/00295871027/1904100501/0043.xml | 1904 | 200 | 1535523 | 纯第三方叙述 |
| 29 | `raw/jl_1905_thebeatricedaily_286.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_europeanstarling_ver01/data/sn84020107/00542866329/1905052301/0609.xml | 1905 | 200 | 691258 | 纯第三方叙述 |
| 30 | `raw/jl_1905_vilascountynews_220.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_clearwater_ver01/data/sn85040613/00514150990/1905060501/0318.xml | 1905 | 200 | 922374 | 纯第三方叙述 |
| 31 | `raw/jl_1905_aberdeenherald_373.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_hoh_ver01/data/sn87093220/00200290379/1905100901/0641.xml | 1905 | 200 | 628121 | 纯第三方叙述 |
| 32 | `raw/jl_1905_newyorktribune_492.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mexico_ver02/data/sn83030214/00175041357/1905121301/0291.xml | 1905 | 200 | 1741928 | 纯第三方叙述 |
| 33 | `raw/jl_1905_newyorktribune_279.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mexico_ver02/data/sn83030214/00175041357/1905123001/0625.xml | 1905 | 200 | 1463403 | 纯第三方叙述 |
| 34 | `raw/jl_1906_thetopekastatejo_292.txt` | https://tile.loc.gov/storage-services/service/ndnp/khi/batch_khi_gygax_ver01/data/sn82016014/00295870965/1906020701/0062.xml | 1906 | 200 | 1219820 | 纯第三方叙述 |
| 35 | `raw/jl_1906_thenewyorkherald_585.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_osage_ver01/data/sn83030313/print1906/1906031101/0292.xml | 1906 | 200 | 1085999 | 纯第三方叙述 |
| 36 | `raw/jl_1906_theeveningworld_580.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_quine_ver01/data/sn83030193/175044553/1906031401/0905.xml | 1906 | 200 | 944592 | 纯第三方叙述 |
| 37 | `raw/jl_1906_thecourierjourna_296.txt` | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_basenji_ver01/data/sn83045188/print/1906031701/0456.xml | 1906 | 200 | 1356952 | 纯第三方叙述 |
| 38 | `raw/jl_1907_eveningjournal_269.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_dover_ver01/data/sn85042354/00383343252/1907021301/0186.xml | 1907 | 200 | 907996 | 纯第三方叙述 |
| 39 | `raw/jl_1907_dailykennebecjou_367.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_burdin_ver03/data/sn82014248/00513682402/1907041201/0123.xml | 1907 | 200 | 1139328 | 纯第三方叙述 |
| 40 | `raw/jl_1907_dailykennebecjou_365.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_burdin_ver03/data/sn82014248/00513682402/1907062501/0848.xml | 1907 | 200 | 1193913 | 纯第三方叙述 |
| 41 | `raw/jl_1907_newyorktribune_240.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jamaica_ver02/data/sn83030214/00175039259/1907100101/0007.xml | 1907 | 200 | 1733293 | 纯第三方叙述 |
| 42 | `raw/jl_1907_santafenewmexica_398.txt` | https://tile.loc.gov/storage-services/service/ndnp/nmu/batch_nmu_huxley_ver01/data/sn84020630/00416150266/1907113001/1055.xml | 1907 | 200 | 815204 | 纯第三方叙述 |
| 43 | `raw/jl_1907_thesun_363.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_hypatia_ver01/data/sn83030272/100481339/1907113001/0478.xml | 1907 | 200 | 2734582 | 纯第三方叙述 |
| 44 | `raw/jl_1907_americustimesrec_031.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_ara_ver01/data/sn89053204/00393344350/1907120101/0783.xml | 1907 | 200 | 395363 | 纯第三方叙述 |
| 45 | `raw/jl_1907_yorkvilleenquire_486.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_dogwood_ver01/data/sn84026925/00295861563/1907120301/0417.xml | 1907 | 200 | 2050876 | 纯第三方叙述 |
| 46 | `raw/jl_1907_springfieldweekl_488.txt` | https://tile.loc.gov/storage-services/service/ndnp/mb/batch_mb_lachesis_ver01/data/sn83020847/00517171268/1907120501/0773.xml | 1907 | 200 | 1806261 | 纯第三方叙述 |
| 47 | `raw/jl_1907_thebolivarcounty_489.txt` | https://tile.loc.gov/storage-services/service/ndnp/msar/batch_msar_emerald_ver02/data/sn87065645/00414212608/1907120701/0670.xml | 1907 | 200 | 1265218 | 纯第三方叙述 |
| 48 | `raw/jl_1907_thedailyintermou_415.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_fonda_ver01/data/sn86092279/00517011101/1907121101/0255.xml | 1907 | 200 | 519122 | 纯第三方叙述 |
| 49 | `raw/jl_1907_themirror_078.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_disco_ver01/data/sn90060762/00199919805/1907121201/0413.xml | 1907 | 200 | 517896 | 纯第三方叙述 |
| 50 | `raw/jl_1907_themirror_079.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_disco_ver01/data/sn90060762/00199919805/1907121201/0414.xml | 1907 | 200 | 524955 | 纯第三方叙述 |
| 51 | `raw/jl_1907_thesanantoniolig_118.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_icaria_ver01/data/sn86090330/00517175237/1907121201/0919.xml | 1907 | 200 | 954867 | 纯第三方叙述 |
| 52 | `raw/jl_1907_thenewhavenunion_479.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_general_ver01/data/sn92051126/00517174099/1907121301/0833.xml | 1907 | 200 | 1122352 | 纯第三方叙述 |
| 53 | `raw/jl_1907_thebaltimorecoun_434.txt` | https://tile.loc.gov/storage-services/service/ndnp/mdu/batch_mdu_indianhead_ver01/data/sn83016368/00415627452/1907121401/0439.xml | 1907 | 200 | 1036582 | 纯第三方叙述 |
| 54 | `raw/jl_1907_thepacificcommer_539.txt` | https://tile.loc.gov/storage-services/service/ndnp/hihouml/batch_hihouml_gonzalo_ver01/data/sn85047084/0029455757A/1907121401/0489.xml | 1907 | 200 | 577663 | 纯第三方叙述 |
| 55 | `raw/jl_1907_thebillingsgazet_487.txt` | https://tile.loc.gov/storage-services/service/ndnp/mthi/batch_mthi_lynx_ver01/data/sn84036008/00212476584/1907121701/0805.xml | 1907 | 200 | 1204602 | 纯第三方叙述 |
| 56 | `raw/jl_1907_thewashingtontim_500.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_romeo_ver02/data/sn84026749/100492738/1907122401/0589.xml | 1907 | 200 | 1242652 | 纯第三方叙述 |
| 57 | `raw/jl_1907_thecolumbian_128.txt` | https://tile.loc.gov/storage-services/service/ndnp/pst/batch_pst_irvin_ver01/data/sn83032011/00280776890/1907122601/0880.xml | 1907 | 200 | 681209 | 纯第三方叙述 |
| 58 | `raw/jl_1908_thesun_371.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_iqbal_ver01/data/sn83030272/100481340/1908011201/0177.xml | 1908 | 200 | 2521302 | 纯第三方叙述 |
| 59 | `raw/jl_1908_theleecountyjour_081.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/sn89053337/00517010431/1908012401/0027.xml | 1908 | 200 | 609641 | 纯第三方叙述 |
| 60 | `raw/jl_1908_thesavannahtribu_108.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_inugami_ver01/data/sn84020323/00517177817/1908012501/0350.xml | 1908 | 200 | 664140 | 纯第三方叙述 |
| 61 | `raw/jl_1908_thewheatlandworl_137.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_aarakocra_ver01/data/sn92066906/0054286218A/1908020701/0898.xml | 1908 | 200 | 657326 | 纯第三方叙述 |
| 62 | `raw/jl_1908_thecourierjourna_298.txt` | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_basenji_ver01/data/sn83045188/print/1908042401/0738.xml | 1908 | 200 | 1726129 | 纯第三方叙述 |
| 63 | `raw/jl_1908_oxforddemocrat_369.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524196/1908051201/0292.xml | 1908 | 200 | 1871761 | 纯第三方叙述 |
| 64 | `raw/jl_1908_thenewsdemocrat_282.txt` | https://tile.loc.gov/storage-services/service/ndnp/rp/batch_rp_crawlingclaw_ver03/data/sn91070633/0051415384A/1908051501/0959.xml | 1908 | 200 | 959313 | **含本人直引** |
| 65 | `raw/jl_1908_themanningtimes_206.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_babytate_ver01/data/sn86063760/00294550665/1908052001/0265.xml | 1908 | 200 | 1376862 | 纯第三方叙述 |
| 66 | `raw/jl_1908_themanningtimes_212.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_babytate_ver01/data/sn86063760/00294550665/1908052001/0265.xml | 1908 | 200 | 1376862 | 纯第三方叙述 |
| 67 | `raw/jl_1908_kingsburycountyi_293.txt` | https://tile.loc.gov/storage-services/service/ndnp/sdhi/batch_sdhi_apple_ver01/data/sn00065130/00279522801/1908052201/0728.xml | 1908 | 200 | 986493 | 纯第三方叙述 |
| 68 | `raw/jl_1908_thesun_313.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_mill_ver01/data/sn83030272/100481376/1908072801/0184.xml | 1908 | 200 | 1669075 | 纯第三方叙述 |
| 69 | `raw/jl_1908_thebirminghamage_011.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_flagg_ver01/data/sn85038485/00340583838/1908080701/0476.xml | 1908 | 200 | 958197 | 纯第三方叙述 |
| 70 | `raw/jl_1908_newyorktribune_049.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_brazil_ver03/data/sn83030214/00175039387/1908081201/0223.xml | 1908 | 200 | 1381691 | 纯第三方叙述 |
| 71 | `raw/jl_1908_theeveningworld_203.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_russell_ver01/data/sn83030193/175044693/1908081201/0471.xml | 1908 | 200 | 1194230 | 纯第三方叙述 |
| 72 | `raw/jl_1908_theeveningworld_255.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_russell_ver01/data/sn83030193/175044693/1908081201/0471.xml | 1908 | 200 | 1194230 | 纯第三方叙述 |
| 73 | `raw/jl_1908_thenewsdemocrat_201.txt` | https://tile.loc.gov/storage-services/service/ndnp/rp/batch_rp_crawlingclaw_ver03/data/sn91070633/00514153851/1908081401/0307.xml | 1908 | 200 | 1064410 | 纯第三方叙述 |
| 74 | `raw/jl_1908_thenewsdemocrat_224.txt` | https://tile.loc.gov/storage-services/service/ndnp/rp/batch_rp_crawlingclaw_ver03/data/sn91070633/00514153851/1908081401/0307.xml | 1908 | 200 | 1064410 | 纯第三方叙述 |
| 75 | `raw/jl_1908_thedetroittimes_215.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_edenville_ver01/data/sn83016689/00279551485/1908082002/0106.xml | 1908 | 200 | 1025428 | 纯第三方叙述 |
| 76 | `raw/jl_1908_thewashingtontim_204.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_tango_ver02/data/sn84026749/100492714/1908082001/0339.xml | 1908 | 200 | 1070830 | 纯第三方叙述 |
| 77 | `raw/jl_1908_thewashingtontim_260.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_tango_ver02/data/sn84026749/100492714/1908082001/0339.xml | 1908 | 200 | 1070830 | 纯第三方叙述 |
| 78 | `raw/jl_1908_thedetroittimes_210.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_edenville_ver01/data/sn83016689/00279551485/1908082101/0126.xml | 1908 | 200 | 580625 | 纯第三方叙述 |
| 79 | `raw/jl_1908_laredoweeklytime_207.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_albatross_ver01/data/sn86089566/00517176382/1908082301/0377.xml | 1908 | 200 | 642983 | 纯第三方叙述 |
| 80 | `raw/jl_1908_laredoweeklytime_266.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_albatross_ver01/data/sn86089566/00517176382/1908082301/0377.xml | 1908 | 200 | 642983 | 纯第三方叙述 |
| 81 | `raw/jl_1908_thefrontier_213.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_keithsbear_ver03/data/2010270509/00393345809/1908082701/0053.xml | 1908 | 200 | 1012956 | 纯第三方叙述 |
| 82 | `raw/jl_1908_theleecountyjour_131.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/sn89053337/00517010431/1908082801/0269.xml | 1908 | 200 | 764415 | 纯第三方叙述 |
| 83 | `raw/jl_1908_newyorktribune_237.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_brazil_ver03/data/sn83030214/00175039387/1908082901/0521.xml | 1908 | 200 | 1602053 | 纯第三方叙述 |
| 84 | `raw/jl_1908_thesun_230.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_mill_ver01/data/sn83030272/100481376/1908090401/0671.xml | 1908 | 200 | 1330757 | 纯第三方叙述 |
| 85 | `raw/jl_1908_newyorktribune_040.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_brazil_ver03/data/sn83030214/00175039399/1908090501/0053.xml | 1908 | 200 | 1341148 | 纯第三方叙述 |
| 86 | `raw/jl_1908_themadisondailyl_140.txt` | https://tile.loc.gov/storage-services/service/ndnp/sdhi/batch_sdhi_grenada_ver01/data/sn99062034/00279523246/1908090501/1208.xml | 1908 | 200 | 629543 | 纯第三方叙述 |
| 87 | `raw/jl_1908_bryanmorningeagl_096.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_infiniti_ver03/data/sn86088652/00200297064/1908090601/0692.xml | 1908 | 200 | 799208 | 纯第三方叙述 |
| 88 | `raw/jl_1908_thetopekastatejo_263.txt` | https://tile.loc.gov/storage-services/service/ndnp/khi/batch_khi_forbes_ver01/data/sn82016014/00295870825/1908121401/0381.xml | 1908 | 200 | 905583 | 纯第三方叙述 |
| 89 | `raw/jl_1909_thesun_307.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_james_ver01/data/sn83030272/100481406/1909040901/0802.xml | 1909 | 200 | 2488839 | 纯第三方叙述 |
| 90 | `raw/jl_1909_thedailymissouli_481.txt` | https://tile.loc.gov/storage-services/service/ndnp/mthi/batch_mthi_dragonfly_ver01/data/sn83025316/00294554609/1909042101/1312.xml | 1909 | 200 | 649671 | 纯第三方叙述 |
| 91 | `raw/jl_1909_themitchellcapit_435.txt` | https://tile.loc.gov/storage-services/service/ndnp/sdhi/batch_sdhi_hawk_ver01/data/sn2001063112/00415624712/1909042201/1030.xml | 1909 | 200 | 928957 | 纯第三方叙述 |
| 92 | `raw/jl_1909_newyorktribune_468.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_iceland_ver02/data/sn83030214/00175039491/1909042601/0540.xml | 1909 | 200 | 1611295 | 纯第三方叙述 |
| 93 | `raw/jl_1909_bismarckdailytri_205.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_drake_ver01/data/sn85042242/0021247843A/1909042701/0778.xml | 1909 | 200 | 714273 | 纯第三方叙述 |
| 94 | `raw/jl_1909_bismarckdailytri_222.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_drake_ver01/data/sn85042242/0021247843A/1909042701/0778.xml | 1909 | 200 | 714273 | 纯第三方叙述 |
| 95 | `raw/jl_1909_kingsburycountyi_447.txt` | https://tile.loc.gov/storage-services/service/ndnp/sdhi/batch_sdhi_apple_ver01/data/sn00065130/00279522801/1909043001/1115.xml | 1909 | 200 | 1227664 | 纯第三方叙述 |
| 96 | `raw/jl_1909_theeveningstates_076.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_elwha_ver01/data/sn88085421/00237282966/1909050101/0087.xml | 1909 | 200 | 478971 | 纯第三方叙述 |
| 97 | `raw/jl_1909_thebarredailytim_464.txt` | https://tile.loc.gov/storage-services/service/ndnp/vtu/batch_vtu_cauliflower_ver01/data/sn91066782/00415628195/1909050401/0220.xml | 1909 | 200 | 1247173 | 纯第三方叙述 |
| 98 | `raw/jl_1909_bridgetonpioneer_391.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_ketchup_ver01/data/sn87068192/00279529741/1909050601/0574.xml | 1909 | 200 | 793177 | 纯第三方叙述 |
| 99 | `raw/jl_1909_milfordchronicle_041.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_catwoman_ver01/data/sn87062224/00514156426/1909050701/0168.xml | 1909 | 200 | 431287 | 纯第三方叙述 |
| 100 | `raw/jl_1909_martinsburgheral_453.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_casper_ver01/data/sn85059533/00393349165/1909050801/0577.xml | 1909 | 200 | 751070 | 纯第三方叙述 |
| 101 | `raw/jl_1909_theriverpress_208.txt` | https://tile.loc.gov/storage-services/service/ndnp/mthi/batch_mthi_crane_ver01/data/sn85053157/00295860881/1909051901/0165.xml | 1909 | 200 | 662580 | 纯第三方叙述 |
| 102 | `raw/jl_1909_theriverpress_234.txt` | https://tile.loc.gov/storage-services/service/ndnp/mthi/batch_mthi_crane_ver01/data/sn85053157/00295860881/1909051901/0165.xml | 1909 | 200 | 662580 | 纯第三方叙述 |
| 103 | `raw/jl_1909_oxforddemocrat_366.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524196/1909060801/0518.xml | 1909 | 200 | 1498805 | 纯第三方叙述 |
| 104 | `raw/jl_1909_thebridgeporteve_380.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_lebanon_ver03/data/sn84022472/00415629822/1909071401/0119.xml | 1909 | 200 | 1273219 | 纯第三方叙述 |
| 105 | `raw/jl_1909_thebridgeporteve_246.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_lebanon_ver03/data/sn84022472/00415629822/1909072101/0185.xml | 1909 | 200 | 636303 | 纯第三方叙述 |
| 106 | `raw/jl_1909_thenewarkstarand_424.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_bacala_ver01/data/sn91064010/00332896039/1909080701/0460.xml | 1909 | 200 | 961374 | 纯第三方叙述 |
| 107 | `raw/jl_1909_thelamarregister_456.txt` | https://tile.loc.gov/storage-services/service/ndnp/cohi/batch_cohi_dorchester_ver01/data/sn86063147/00340585951/1909081101/1228.xml | 1909 | 200 | 902813 | 纯第三方叙述 |
| 108 | `raw/jl_1909_thesun_265.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_james_ver01/data/sn83030272/10048142A/1909081101/0590.xml | 1909 | 200 | 2217469 | 纯第三方叙述 |
| 109 | `raw/jl_1909_ladysmithnewsbud_448.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_knarl_ver02/data/sn85040245/00414215415/1909081201/0079.xml | 1909 | 200 | 1153549 | 纯第三方叙述 |
| 110 | `raw/jl_1909_theelbertcountyt_455.txt` | https://tile.loc.gov/storage-services/service/ndnp/cohi/batch_cohi_jasper_ver01/data/sn90051300/0034058613A/1909081201/0582.xml | 1909 | 200 | 870506 | 纯第三方叙述 |
| 111 | `raw/jl_1909_perrysburgjourna_141.txt` | https://tile.loc.gov/storage-services/service/ndnp/ohi/batch_ohi_golf_ver04/data/sn87076843/00237289080/1909081301/0237.xml | 1909 | 200 | 723453 | 纯第三方叙述 |
| 112 | `raw/jl_1909_thespokanepress_088.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_columbia_ver01/data/sn88085947/00211108605/1909081301/0640.xml | 1909 | 200 | 556075 | 纯第三方叙述 |
| 113 | `raw/jl_1909_thespokanepress_090.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_columbia_ver01/data/sn88085947/00211108605/1909081301/0639.xml | 1909 | 200 | 560172 | 纯第三方叙述 |
| 114 | `raw/jl_1909_theappeal_393.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_effie_ver01/data/sn83016810/00280768030/1909081401/0187.xml | 1909 | 200 | 714643 | 纯第三方叙述 |
| 115 | `raw/jl_1909_thevirginiaenter_425.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_lexus_ver01/data/sn90059180/00212472165/1909101501/0383.xml | 1909 | 200 | 920602 | 纯第三方叙述 |
| 116 | `raw/jl_1910_thesanfranciscoc_288.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_jenner_ver01/data/sn85066387/00175046550/1910022701/0644.xml | 1910 | 200 | 1629287 | 纯第三方叙述 |
| 117 | `raw/jl_1910_losangelesherald_259.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_rubidoux_ver01/data/sn85042462/00175035850/1910040801/0916.xml | 1910 | 200 | 918129 | 纯第三方叙述 |
| 118 | `raw/jl_1910_thelaborjournal_328.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_american_ver02/data/sn88085620/00211107601/1910041501/0296.xml | 1910 | 200 | 825636 | 纯第三方叙述 |
| 119 | `raw/jl_1910_thewashingtontim_133.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_whiskey_ver02/data/sn84026749/0010049274A/1910052601/0117.xml | 1910 | 200 | 835794 | 纯第三方叙述 |
| 120 | `raw/jl_1910_thedetroittimes_023.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_gulliver_ver01/data/sn83016689/00279551680/1910082001/0002.xml | 1910 | 200 | 1041663 | **含本人直引** |
| 121 | `raw/jl_1910_thedetroittimes_423.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_gulliver_ver01/data/sn83016689/00279551680/1910082002/0038.xml | 1910 | 200 | 1072770 | 纯第三方叙述 |
| 122 | `raw/jl_1910_thetacomatimes_397.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_elm_ver01/data/sn88085187/00211108186/1910082501/1066.xml | 1910 | 200 | 845398 | 纯第三方叙述 |
| 123 | `raw/jl_1910_thetopekastatejo_252.txt` | https://tile.loc.gov/storage-services/service/ndnp/khi/batch_khi_edelbrock_ver01/data/sn82016014/00295870709/1910120801/0106.xml | 1910 | 200 | 1253999 | 纯第三方叙述 |
| 124 | `raw/jl_1911_eaststlouisdaily_545.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_egret_ver01/data/sn92053737/00542864667/1911010801/0751.xml | 1911 | 200 | 862395 | 纯第三方叙述 |
| 125 | `raw/jl_1911_theprescottdaily_535.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_gyarados_ver01/data/sn90050307/00414212906/1911010901/0754.xml | 1911 | 200 | 491701 | 纯第三方叙述 |
| 126 | `raw/jl_1911_potosijournal_546.txt` | https://tile.loc.gov/storage-services/service/ndnp/mohi/batch_mohi_marmaduke_ver02/data/sn90061371/00294557180/1911011101/0349.xml | 1911 | 200 | 948029 | 纯第三方叙述 |
| 127 | `raw/jl_1911_ironcountyregist_552.txt` | https://tile.loc.gov/storage-services/service/ndnp/mohi/batch_mohi_igoo_ver01/data/sn84024283/00294556746/1911011201/0444.xml | 1911 | 200 | 1020075 | 纯第三方叙述 |
| 128 | `raw/jl_1911_eveningtimesrepu_242.txt` | https://tile.loc.gov/storage-services/service/ndnp/iahi/batch_iahi_imogene_ver01/data/sn85049554/00295875719/1911071301/0670.xml | 1911 | 200 | 997108 | 纯第三方叙述 |
| 129 | `raw/jl_1911_eastoregonianeo_231.txt` | https://tile.loc.gov/storage-services/service/ndnp/oru/batch_oru_mallard_ver02/data/sn88086023/00202194497/1911102801/0919.xml | 1911 | 200 | 706992 | 纯第三方叙述 |
| 130 | `raw/jl_1912_dailykennebecjou_446.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_debsconeag_ver01/data/sn82014248/00513682724/1912092401/0350.xml | 1912 | 200 | 907250 | 纯第三方叙述 |
| 131 | `raw/jl_1912_newhampshirefarm_483.txt` | https://tile.loc.gov/storage-services/service/ndnp/nhd/batch_nhd_doublehead_ver02/data/sn90062374/00517015532/1912092501/0461.xml | 1912 | 200 | 1871212 | 纯第三方叙述 |
| 132 | `raw/jl_1912_leprogrs_476.txt` | https://tile.loc.gov/storage-services/service/ndnp/rp/batch_rp_barbeddevil_ver02/data/sn83045044/00513689330/1912092701/0078.xml | 1912 | 200 | 1092783 | 纯第三方叙述 |
| 133 | `raw/jl_1912_martinsburgstate_457.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_els_ver01/data/sn85059542/00393349074/1912092701/0295.xml | 1912 | 200 | 809488 | 纯第三方叙述 |
| 134 | `raw/jl_1912_martinsburgheral_467.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_casper_ver01/data/sn85059533/00393349177/1912092801/0501.xml | 1912 | 200 | 885337 | 纯第三方叙述 |
| 135 | `raw/jl_1912_thesanfranciscoc_248.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_elderwood_ver02/data/sn85066387/00280768480/1912123101/0433.xml | 1912 | 200 | 1989149 | 纯第三方叙述 |
| 136 | `raw/jl_1913_thesanfranciscoc_236.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_elderwood_ver02/data/sn85066387/00280768546/1913032301/0277.xml | 1913 | 200 | 1893510 | 纯第三方叙述 |
| 137 | `raw/jl_1913_theidahorepublic_254.txt` | https://tile.loc.gov/storage-services/service/ndnp/idhi/batch_idhi_fraser_ver01/data/sn86091197/00415666640/1913040401/0112.xml | 1913 | 200 | 882903 | 纯第三方叙述 |
| 138 | `raw/jl_1913_laredoweeklytime_272.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_albatross_ver01/data/sn86089566/00517176400/1913080301/0942.xml | 1913 | 200 | 904301 | 纯第三方叙述 |
| 139 | `raw/jl_1913_thesanfranciscoc_241.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_grimes_ver01/data/sn85066387/00280768637/1913080301/0109.xml | 1913 | 200 | 1803661 | 纯第三方叙述 |
| 140 | `raw/jl_1913_thesanfranciscoc_323.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_grimes_ver01/data/sn86064451/00280768686/1913121301/0223.xml | 1913 | 200 | 1816058 | 纯第三方叙述 |
| 141 | `raw/jl_1913_thebridgeporteve_372.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_fairfield_ver01/data/sn84022472/00295867243/1913123101/0374.xml | 1913 | 200 | 1008080 | 纯第三方叙述 |
| 142 | `raw/jl_1914_thebirminghamage_512.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_inman_ver01/data/sn85038485/00340582615/1914010401/0084.xml | 1914 | 200 | 909390 | 纯第三方叙述 |
| 143 | `raw/jl_1914_thechickashadail_591.txt` | https://tile.loc.gov/storage-services/service/ndnp/okhi/batch_okhi_gruyere_ver01/data/sn86090528/0029586431A/1914061001/0513.xml | 1914 | 200 | 392036 | 纯第三方叙述 |
| 144 | `raw/jl_1914_theleonreporter_579.txt` | https://tile.loc.gov/storage-services/service/ndnp/iahi/batch_iahi_bettendorf_ver01/data/sn87057096/00202198466/1914070901/0362.xml | 1914 | 200 | 802109 | 纯第三方叙述 |
| 145 | `raw/jl_1915_thebarredailytim_226.txt` | https://tile.loc.gov/storage-services/service/ndnp/vtu/batch_vtu_daikon_ver01/data/sn91066782/00415629928/1915013001/0209.xml | 1915 | 200 | 1091613 | 纯第三方叙述 |
| 146 | `raw/jl_1915_thewashingtonher_235.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_braniff_ver01/data/sn83045433/00237288543/1915013001/0429.xml | 1915 | 200 | 1119583 | 纯第三方叙述 |
| 147 | `raw/jl_1915_norwichbulletin_299.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_andover_ver01/data/sn82014086/00295865970/1915020901/0400.xml | 1915 | 200 | 1357446 | 纯第三方叙述 |
| 148 | `raw/jl_1915_theeveningworld_574.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_janet_ver01/data/sn83030193/00280766094/1915021701/0648.xml | 1915 | 200 | 933054 | 纯第三方叙述 |
| 149 | `raw/jl_1915_imperialvalleypr_572.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_mesquite_ver02/data/sn92070146/00414189465/1915021801/0180.xml | 1915 | 200 | 429165 | 纯第三方叙述 |
| 150 | `raw/jl_1915_thewashingtonher_573.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_frontier_ver01/data/sn83045433/00237288531/1915021801/0045.xml | 1915 | 200 | 853639 | 纯第三方叙述 |
| 151 | `raw/jl_1915_thelaramierepubl_510.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_crichton_ver01/data/sn92066979/0051368762A/1915022701/0624.xml | 1915 | 200 | 538580 | 纯第三方叙述 |
| 152 | `raw/jl_1915_thefargoforumand_571.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_klingon_ver01/data/sn85042224/00383345583/1915030601/0652.xml | 1915 | 200 | 1068903 | 纯第三方叙述 |
| 153 | `raw/jl_1915_thedetroittimes_589.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_leonidas_ver01/data/sn83016689/00279552258/1915031901/0521.xml | 1915 | 200 | 787612 | 纯第三方叙述 |
| 154 | `raw/jl_1915_thedetroittimes_314.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_leonidas_ver01/data/sn83016689/00279552258/1915032601/0714.xml | 1915 | 200 | 1292440 | 纯第三方叙述 |
| 155 | `raw/jl_1915_thesundaytelegra_569.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_oliver_ver01/data/sn85059732/00415660911/1915032801/0114.xml | 1915 | 200 | 889931 | 纯第三方叙述 |
| 156 | `raw/jl_1915_thelansesentinel_522.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_kalkaska_ver01/data/sn96077142/00271764376/1915041001/0388.xml | 1915 | 200 | 417106 | 纯第三方叙述 |
| 157 | `raw/jl_1915_thebrattleboroda_577.txt` | https://tile.loc.gov/storage-services/service/ndnp/vtu/batch_vtu_garlic_ver01/data/sn86071593/00415627737/1915060101/0325.xml | 1915 | 200 | 1059809 | 纯第三方叙述 |
| 158 | `raw/jl_1915_thebenningtoneve_576.txt` | https://tile.loc.gov/storage-services/service/ndnp/vtu/batch_vtu_canaan_ver02/data/sn95066012/00202196652/1915060401/0305.xml | 1915 | 200 | 939154 | 纯第三方叙述 |
| 159 | `raw/jl_1915_thedemocraticadv_047.txt` | https://tile.loc.gov/storage-services/service/ndnp/mdu/batch_mdu_elsberg_ver02/data/sn85038292/00415624153/1915061101/0210.xml | 1915 | 200 | 1298137 | 纯第三方叙述 |
| 160 | `raw/jl_1915_bridgetonpioneer_130.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_ketchup_ver01/data/sn87068192/00279529777/1915070801/0640.xml | 1915 | 200 | 672013 | 纯第三方叙述 |
| 161 | `raw/jl_1915_thehartfordrepub_592.txt` | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_fernico_ver01/data/sn86069313/00280762842/1915082001/0714.xml | 1915 | 200 | 472999 | 纯第三方叙述 |
| 162 | `raw/jl_1915_eveningtimesrepu_583.txt` | https://tile.loc.gov/storage-services/service/ndnp/iahi/batch_iahi_kalona_ver01/data/sn85049554/00295876992/1915111501/0741.xml | 1915 | 200 | 681097 | 纯第三方叙述 |
| 163 | `raw/jl_1915_eveningstar_044.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_ixtl_ver01/data/sn83045462/0028065873A/1915112801/0046.xml | 1915 | 200 | 301695 | 纯第三方叙述 |
| 164 | `raw/jl_1916_eveningstar_527.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jabbathehut_ver01/data/sn83045462/00280658741/1916010901/0536.xml | 1916 | 200 | 405963 | 纯第三方叙述 |
| 165 | `raw/jl_1916_thebrattleboroda_575.txt` | https://tile.loc.gov/storage-services/service/ndnp/vtu/batch_vtu_garlic_ver01/data/sn86071593/00415627762/1916021601/0248.xml | 1916 | 200 | 767658 | 纯第三方叙述 |
| 166 | `raw/jl_1916_eveningstar_531.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jabbathehut_ver01/data/sn83045462/00280658765/1916022001/0324.xml | 1916 | 200 | 458256 | 纯第三方叙述 |
| 167 | `raw/jl_1916_thebridgeporteve_376.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_goshen_ver01/data/sn84022472/00295867176/1916090801/0094.xml | 1916 | 200 | 949604 | 纯第三方叙述 |
| 168 | `raw/jl_1916_theindependentre_358.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_harpswell_ver01/data/sn96075050/0033289559A/1916092101/0879.xml | 1916 | 200 | 1026246 | 纯第三方叙述 |
| 169 | `raw/jl_1917_oxforddemocrat_348.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917010201/0218.xml | 1917 | 200 | 1873728 | 纯第三方叙述 |
| 170 | `raw/jl_1917_thewashingtontim_326.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_iberia_ver01/data/sn84026749/0028076436A/1917011101/0148.xml | 1917 | 200 | 656544 | 纯第三方叙述 |
| 171 | `raw/jl_1917_keoweecourier_325.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_imanidevore_ver02/data/sn84026912/00294558858/1917011701/0388.xml | 1917 | 200 | 723290 | 纯第三方叙述 |
| 172 | `raw/jl_1917_theindependentre_351.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_harpswell_ver01/data/sn96075050/00340587856/1917011801/0029.xml | 1917 | 200 | 1214951 | 纯第三方叙述 |
| 173 | `raw/jl_1917_pinebluffdailygr_105.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_kraftwerk_ver01/data/sn89051168/00393343461/1917012501/0463.xml | 1917 | 200 | 573654 | 纯第三方叙述 |
| 174 | `raw/jl_1917_oxforddemocrat_334.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917013001/0234.xml | 1917 | 200 | 1497340 | 纯第三方叙述 |
| 175 | `raw/jl_1917_thedawsonnews_350.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_beaker_ver01/data/sn89053283/0051717709A/1917013001/0052.xml | 1917 | 200 | 487285 | 纯第三方叙述 |
| 176 | `raw/jl_1917_newyorktribune_135.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_thompson_ver02/data/sn83030214/00206532117/1917021601/0315.xml | 1917 | 200 | 734049 | 纯第三方叙述 |
| 177 | `raw/jl_1917_thebirminghamage_073.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_ayler_ver01/data/sn85038485/00340583772/1917021601/0606.xml | 1917 | 200 | 673419 | 纯第三方叙述 |
| 178 | `raw/jl_1917_thebirminghamage_100.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_ayler_ver01/data/sn85038485/00340583772/1917021701/0625.xml | 1917 | 200 | 794921 | 纯第三方叙述 |
| 179 | `raw/jl_1917_arkansasecho_117.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_cosmic_ver01/data/sn88084068/00513688106/1917030101/0229.xml | 1917 | 200 | 720252 | 纯第三方叙述 |
| 180 | `raw/jl_1917_theindependentre_357.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_harpswell_ver01/data/sn96075050/00340587856/1917030101/0078.xml | 1917 | 200 | 1042159 | 纯第三方叙述 |
| 181 | `raw/jl_1917_oxforddemocrat_360.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917032701/0267.xml | 1917 | 200 | 1676442 | 纯第三方叙述 |
| 182 | `raw/jl_1917_dailykennebecjou_354.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683108/1917040301/0369.xml | 1917 | 200 | 1112656 | 纯第三方叙述 |
| 183 | `raw/jl_1917_newhampshirefarm_324.txt` | https://tile.loc.gov/storage-services/service/ndnp/nhd/batch_nhd_doublehead_ver02/data/sn90062374/00517015489/1917041801/0159.xml | 1917 | 200 | 1905423 | 纯第三方叙述 |
| 184 | `raw/jl_1917_oxforddemocrat_332.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917042401/0282.xml | 1917 | 200 | 1718070 | 纯第三方叙述 |
| 185 | `raw/jl_1917_themonitor_015.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_indescribablebeast_ver01/data/00225879/00332899223/1917042801/0882.xml | 1917 | 200 | 272093 | 纯第三方叙述 |
| 186 | `raw/jl_1917_oxforddemocrat_347.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917050101/0286.xml | 1917 | 200 | 1811915 | 纯第三方叙述 |
| 187 | `raw/jl_1917_oxforddemocrat_327.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917050801/0290.xml | 1917 | 200 | 1793098 | 纯第三方叙述 |
| 188 | `raw/jl_1917_dailykennebecjou_257.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/0051368311A/1917051501/0184.xml | 1917 | 200 | 1142215 | 纯第三方叙述 |
| 189 | `raw/jl_1917_dailykennebecjou_329.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/0051368311A/1917052201/0262.xml | 1917 | 200 | 1254011 | 纯第三方叙述 |
| 190 | `raw/jl_1917_therepublicanjou_338.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_damariscotta_ver02/data/sn78000873/00279525000/1917071201/0250.xml | 1917 | 200 | 895836 | 纯第三方叙述 |
| 191 | `raw/jl_1917_dailykennebecjou_330.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683121/1917080701/0401.xml | 1917 | 200 | 1007606 | 纯第三方叙述 |
| 192 | `raw/jl_1917_oxforddemocrat_344.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524226/1917081401/0347.xml | 1917 | 200 | 1708436 | 纯第三方叙述 |
| 193 | `raw/jl_1917_theindependentre_340.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_harpswell_ver01/data/sn96075050/00340587856/1917081601/0306.xml | 1917 | 200 | 1239119 | 纯第三方叙述 |
| 194 | `raw/jl_1917_dailykennebecjou_353.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683133/1917100601/0383.xml | 1917 | 200 | 1090928 | 纯第三方叙述 |
| 195 | `raw/jl_1917_thebrattleboroda_331.txt` | https://tile.loc.gov/storage-services/service/ndnp/vtu/batch_vtu_horseradish_ver01/data/sn86071593/00415629461/1917111401/0327.xml | 1917 | 200 | 777134 | 纯第三方叙述 |
| 196 | `raw/jl_1917_themirrorandfarm_370.txt` | https://tile.loc.gov/storage-services/service/ndnp/nhd/batch_nhd_dove_ver01/data/sn84023820/00541315445/1917122701/0414.xml | 1917 | 200 | 1435407 | 纯第三方叙述 |
| 197 | `raw/jl_1918_dailykennebecjou_238.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683157/1918020401/0311.xml | 1918 | 200 | 1144041 | 纯第三方叙述 |
| 198 | `raw/jl_1918_newyorktribune_311.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_allen_ver02/data/sn83030214/00206532257/1918041402/0301.xml | 1918 | 200 | 969673 | 纯第三方叙述 |
| 199 | `raw/jl_1918_thesun_343.txt` | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_odum_ver01/data/sn83030431/0020029404A/1918050501/0844.xml | 1918 | 200 | 2162739 | 纯第三方叙述 |
| 200 | `raw/jl_1918_dailykennebecjou_341.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683170/1918061101/0376.xml | 1918 | 200 | 1114129 | 纯第三方叙述 |
| 201 | `raw/jl_1918_dailykennebecjou_356.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683182/1918073001/0251.xml | 1918 | 200 | 766689 | 纯第三方叙述 |
| 202 | `raw/jl_1918_dailykennebecjou_339.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/00513683182/1918082701/0473.xml | 1918 | 200 | 884977 | 纯第三方叙述 |
| 203 | `raw/jl_1919_thealaskadailyem_048.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_jellymoss_ver01/data/sn84020657/00279527033/1919012801/0189.xml | 1919 | 200 | 409848 | 纯第三方叙述 |
| 204 | `raw/jl_1919_theandersonnews_104.txt` | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_heeler_ver01/data/sn86069242/00516998443/1919020601/0043.xml | 1919 | 200 | 618634 | 纯第三方叙述 |
| 205 | `raw/jl_1919_thenewsscimitar_320.txt` | https://tile.loc.gov/storage-services/service/ndnp/tu/batch_tu_carla_ver01/data/sn98069867/00415621656/1919031201/0410.xml | 1919 | 200 | 1610913 | 纯第三方叙述 |
| 206 | `raw/jl_1919_eveningcapitalne_303.txt` | https://tile.loc.gov/storage-services/service/ndnp/idhi/batch_idhi_kingsolver_ver01/data/sn88056024/00295868181/1919032701/0651.xml | 1919 | 200 | 766742 | 纯第三方叙述 |
| 207 | `raw/jl_1919_newyorktribune_217.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_carril_ver02/data/sn83030214/00206532385/1919042501/0688.xml | 1919 | 200 | 1038101 | 纯第三方叙述 |
| 208 | `raw/jl_1919_auduboncountyjou_291.txt` | https://tile.loc.gov/storage-services/service/ndnp/iahi/batch_iahi_kutcher_ver01/data/sn87057934/00415622715/1919060501/0801.xml | 1919 | 200 | 840700 | 纯第三方叙述 |
| 209 | `raw/jl_1919_thewatchmanandso_300.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_heddalettuce_ver01/data/sn93067846/0029455094A/1919072301/0087.xml | 1919 | 200 | 694192 | 纯第三方叙述 |
| 210 | `raw/jl_1919_dailykennebecjou_335.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_forestcity_ver02/data/sn82014248/0051368292A/1919081901/0431.xml | 1919 | 200 | 1005320 | 纯第三方叙述 |
| 211 | `raw/jl_1920_oxforddemocrat_362.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524238/1920011301/0220.xml | 1920 | 200 | 1393438 | 纯第三方叙述 |
| 212 | `raw/jl_1920_oxforddemocrat_361.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_baxter_ver01/data/sn83009653/00279524238/1920020301/0232.xml | 1920 | 200 | 1604214 | 纯第三方叙述 |
| 213 | `raw/jl_1920_theindependentre_355.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_harpswell_ver01/data/sn96075050/00340587868/1920080501/0822.xml | 1920 | 200 | 1267103 | 纯第三方叙述 |
| 214 | `raw/jl_1920_newyorktribune_233.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eustachy_ver01/data/sn83030214/00206532555/1920092401/0637.xml | 1920 | 200 | 1176680 | 纯第三方叙述 |
| 215 | `raw/jl_1920_casperdailytribu_297.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_frannie_ver01/data/sn86072160/00514150357/1920100601/0038.xml | 1920 | 200 | 888839 | 纯第三方叙述 |
| 216 | `raw/jl_1920_dailykennebecjou_368.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_gilbertville_ver01/data/sn82014248/00513682979/1920112301/0517.xml | 1920 | 200 | 1095875 | 纯第三方叙述 |
| 217 | `raw/jl_1921_omahadailybee_290.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_daleacandida_ver01/data/sn99021999/00280778862/1921011401/0835.xml | 1921 | 200 | 818770 | 纯第三方叙述 |
| 218 | `raw/jl_1921_thebirminghamage_232.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_dean_ver01/data/sn85038485/00340583012/1921011401/0250.xml | 1921 | 200 | 1090843 | 纯第三方叙述 |
| 219 | `raw/jl_1921_eveningjournal_304.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_ironhill_ver01/data/sn85042354/00383342557/1921061401/0269.xml | 1921 | 200 | 1432760 | 纯第三方叙述 |
| 220 | `raw/jl_1921_newyorktribune_228.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_gottfried_ver01/data/sn83030214/00206532683/1921090701/0180.xml | 1921 | 200 | 1492986 | 纯第三方叙述 |
| 221 | `raw/jl_1921_newyorktribune_211.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_gottfried_ver01/data/sn83030214/00206532683/1921092501/0681.xml | 1921 | 200 | 1360440 | 纯第三方叙述 |
| 222 | `raw/jl_1921_newyorktribune_216.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_gottfried_ver01/data/sn83030214/00206532701/1921112701/0800.xml | 1921 | 200 | 1014743 | 纯第三方叙述 |
| 223 | `raw/jl_1922_dailykennebecjou_342.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_gilbertville_ver01/data/sn82014248/00513683029/1922011901/0189.xml | 1922 | 200 | 895034 | 纯第三方叙述 |
| 224 | `raw/jl_1922_newyorktribune_519.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_haskins_ver01/data/sn83030214/00206532725/1922012001/0617.xml | 1922 | 200 | 1320855 | 纯第三方叙述 |
| 225 | `raw/jl_1922_dailykennebecjou_359.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_gilbertville_ver01/data/sn82014248/00513683029/1922033101/0931.xml | 1922 | 200 | 1262254 | 纯第三方叙述 |
| 226 | `raw/jl_1922_eveningstar_523.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_cylon_ver01/data/sn83045462/00280657098/1922040701/0435.xml | 1922 | 200 | 328049 | 纯第三方叙述 |
| 227 | `raw/jl_1922_newyorktribune_501.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_iba_ver01/data/sn83030214/00206532348/1922052901/0833.xml | 1922 | 200 | 1145327 | 纯第三方叙述 |
| 228 | `raw/jl_1922_thewashingtonher_401.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_greyhound_ver02/data/sn83045433/00280764267/1922053101/0644.xml | 1922 | 200 | 869128 | 纯第三方叙述 |
| 229 | `raw/jl_1922_thebridgeporttim_529.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_lebanon_ver03/data/sn92051227/00415621048/1922063001/0542.xml | 1922 | 200 | 887779 | 纯第三方叙述 |
| 230 | `raw/jl_1922_thelaramierepubl_524.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_ellison_ver01/data/sn92066979/00517010108/1922070701/0249.xml | 1922 | 200 | 406435 | 纯第三方叙述 |
| 231 | `raw/jl_1922_thedailystarmirr_528.txt` | https://tile.loc.gov/storage-services/service/ndnp/idhi/batch_idhi_kathmandu_ver02/data/sn89055128/00414211501/1922080101/0756.xml | 1922 | 200 | 545619 | 纯第三方叙述 |
| 232 | `raw/jl_1922_theomahamorningb_383.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_easternredbud_ver01/data/sn84024326/00280778850/1922100301/0882.xml | 1922 | 200 | 1083555 | 纯第三方叙述 |
| 233 | `raw/jl_1922_themilwaukeelead_387.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_feta_ver01/data/sn83045293/00517013274/1922100501/0015.xml | 1922 | 200 | 775959 | 纯第三方叙述 |
| 234 | `raw/jl_1922_albuquerquemorni_218.txt` | https://tile.loc.gov/storage-services/service/ndnp/nmu/batch_nmu_emerson_ver01/data/sn84031081/00415627889/1922100701/0069.xml | 1922 | 200 | 1151119 | 纯第三方叙述 |
| 235 | `raw/jl_1922_newyorktribune_469.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jones_ver01/data/sn83030214/00206532798/1922100801/0272.xml | 1922 | 200 | 1612931 | 纯第三方叙述 |
| 236 | `raw/jl_1922_thenewyorkherald_478.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eucalyptus_ver01/data/sn83045774/00271744377/1922100801/0329.xml | 1922 | 200 | 2087081 | 纯第三方叙述 |
| 237 | `raw/jl_1922_eveningjournal_142.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_jimtown_ver01/data/sn85042354/00383342612/1922100901/0029.xml | 1922 | 200 | 852171 | 纯第三方叙述 |
| 238 | `raw/jl_1922_everyeveningwilm_388.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_jimtown_ver01/data/sn87062237/00383342740/1922100901/0055.xml | 1922 | 200 | 959903 | 纯第三方叙述 |
| 239 | `raw/jl_1922_newyorktribune_461.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jones_ver01/data/sn83030214/00206532798/1922100901/0349.xml | 1922 | 200 | 1335195 | 纯第三方叙述 |
| 240 | `raw/jl_1922_richmondtimesdis_106.txt` | https://tile.loc.gov/storage-services/service/ndnp/vi/batch_vi_xanadu_ver01/data/sn83045389/00296029403/1922100901/0347.xml | 1922 | 200 | 639278 | 纯第三方叙述 |
| 241 | `raw/jl_1922_thebirminghamage_403.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_engle_ver01/data/sn85038485/00340582834/1922100901/0570.xml | 1922 | 200 | 1019002 | 纯第三方叙述 |
| 242 | `raw/jl_1922_thewheelingintel_459.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_klingon_ver01/data/sn86092536/00279550201/1922100901/0368.xml | 1922 | 200 | 853474 | 纯第三方叙述 |
| 243 | `raw/jl_1922_newyorktribune_498.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jones_ver01/data/sn83030214/00206532798/1922101001/0372.xml | 1922 | 200 | 791595 | 纯第三方叙述 |
| 244 | `raw/jl_1922_thewatchmanandso_225.txt` | https://tile.loc.gov/storage-services/service/ndnp/scu/batch_scu_heddalettuce_ver01/data/sn93067846/00294550987/1922101101/0183.xml | 1922 | 200 | 1185189 | 纯第三方叙述 |
| 245 | `raw/jl_1922_theindianapolist_247.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348675/1922101601/0656.xml | 1922 | 200 | 1097718 | **含本人直引** |
| 246 | `raw/jl_1922_thebuffalovoice_419.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_irving_ver01/data/sn92067096/00517179899/1922102001/0683.xml | 1922 | 200 | 1014478 | 纯第三方叙述 |
| 247 | `raw/jl_1922_thethermopolisin_010.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_imp_ver02/data/sn92067173/0051699910A/1922102001/0884.xml | 1922 | 200 | 607015 | 纯第三方叙述 |
| 248 | `raw/jl_1922_thenewyorkherald_070.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eucalyptus_ver01/data/sn83045774/00271744389/1922112601/0866.xml | 1922 | 200 | 535761 | 纯第三方叙述 |
| 249 | `raw/jl_1923_thewashingtontim_016.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/00222253949/1923020501/0471.xml | 1923 | 200 | 783949 | **含本人直引** |
| 250 | `raw/jl_1923_eveningstar_430.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_armstrong_ver02/data/sn83045462/00280657281/1923032001/0198.xml | 1923 | 200 | 1248125 | 纯第三方叙述 |
| 251 | `raw/jl_1923_casperdailytribu_436.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_greybull_ver01/data/sn86072160/00514150436/1923032101/0263.xml | 1923 | 200 | 1056777 | 纯第三方叙述 |
| 252 | `raw/jl_1923_sanantoniolight_050.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_aubrey_ver01/data/sn85060004/00517175973/1923032101/0475.xml | 1923 | 200 | 675178 | 纯第三方叙述 |
| 253 | `raw/jl_1923_theomahamorningb_085.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_haydenstopdog_ver01/data/sn84024326/00332899521/1923032101/0803.xml | 1923 | 200 | 1954429 | 纯第三方叙述 |
| 254 | `raw/jl_1923_thebirminghamage_426.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_engle_ver01/data/sn85038485/0034058286A/1923032201/0470.xml | 1923 | 200 | 1274415 | 纯第三方叙述 |
| 255 | `raw/jl_1923_southbendnewstim_308.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_chapel_ver01/data/sn87055779/00517017632/1923102801/0152.xml | 1923 | 200 | 588614 | 纯第三方叙述 |
| 256 | `raw/jl_1923_themilwaukeelead_337.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_feta_ver01/data/sn83045293/00517012531/1923103001/0549.xml | 1923 | 200 | 1124022 | 纯第三方叙述 |
| 257 | `raw/jl_1923_eveningstar_261.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_beiderbecke_ver01/data/sn83045462/00280657414/1923103101/0226.xml | 1923 | 200 | 1971717 | 纯第三方叙述 |
| 258 | `raw/jl_1923_thewashingtondai_008.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fink_ver02/data/sn82016181/00529045621/1923103103/1176.xml | 1923 | 200 | 487499 | 纯第三方叙述 |
| 259 | `raw/jl_1923_eldoradodailynew_441.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_hauerite_ver01/data/sn88084083/00516990648/1923110101/0950.xml | 1923 | 200 | 1168354 | 纯第三方叙述 |
| 260 | `raw/jl_1923_themilwaukeelead_470.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_feta_ver01/data/sn83045293/00517012531/1923110101/0586.xml | 1923 | 200 | 1410400 | 纯第三方叙述 |
| 261 | `raw/jl_1923_thedoloresstar_264.txt` | https://tile.loc.gov/storage-services/service/ndnp/cohi/batch_cohi_alta_ver01/data/sn86002159/00513680442/1923110201/0870.xml | 1923 | 200 | 1089113 | 纯第三方叙述 |
| 262 | `raw/jl_1923_southbendnewstim_458.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_chapel_ver01/data/sn87055779/00517017632/1923110701/0423.xml | 1923 | 200 | 823836 | 纯第三方叙述 |
| 263 | `raw/jl_1923_eveningstar_283.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_beiderbecke_ver01/data/sn83045462/00280657414/1923110801/0595.xml | 1923 | 200 | 1241065 | 纯第三方叙述 |
| 264 | `raw/jl_1923_thebirminghamage_227.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_foster_ver01/data/sn85038485/00513684101/1923111001/0227.xml | 1923 | 200 | 935877 | 纯第三方叙述 |
| 265 | `raw/jl_1923_americustimesrec_390.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_eridanus_ver02/data/sn89053204/00393343655/1923111301/0388.xml | 1923 | 200 | 914259 | **含本人直引** |
| 266 | `raw/jl_1923_eldoradodailynew_080.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_hauerite_ver01/data/sn88084083/00516990648/1923111301/1064.xml | 1923 | 200 | 515302 | **含本人直引** |
| 267 | `raw/jl_1923_theindianapolist_143.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348742/1923112101/0241.xml | 1923 | 200 | 1401498 | 纯第三方叙述 |
| 268 | `raw/jl_1923_thewashingtontim_420.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/0022225405A/1923112101/0124.xml | 1923 | 200 | 1157720 | 纯第三方叙述 |
| 269 | `raw/jl_1923_belingtonprogres_428.txt` | https://tile.loc.gov/storage-services/service/ndnp/wvu/batch_wvu_kite_ver01/data/sn86092333/00514157741/1923112201/0883.xml | 1923 | 200 | 629913 | 纯第三方叙述 |
| 270 | `raw/jl_1923_themilwaukeelead_465.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_feta_ver01/data/sn83045293/00517013304/1923112301/0243.xml | 1923 | 200 | 1318146 | 纯第三方叙述 |
| 271 | `raw/jl_1923_eaststlouisdaily_381.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_ibis_ver01/data/sn92053739/00529044811/1923120301/0319.xml | 1923 | 200 | 967340 | 纯第三方叙述 |
| 272 | `raw/jl_1923_thewashingtondai_268.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fink_ver02/data/sn82016181/00529045645/1923121902/0730.xml | 1923 | 200 | 305348 | 纯第三方叙述 |
| 273 | `raw/jl_1923_southbendnewstim_414.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_chapel_ver01/data/sn87055779/00517017656/1923122001/0245.xml | 1923 | 200 | 587748 | 纯第三方叙述 |
| 274 | `raw/jl_1923_casperdailytribu_039.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150461/1923122101/0663.xml | 1923 | 200 | 362684 | 纯第三方叙述 |
| 275 | `raw/jl_1923_eveningstar_442.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_beiderbecke_ver01/data/sn83045462/0028065744A/1923122101/0539.xml | 1923 | 200 | 1340483 | 纯第三方叙述 |
| 276 | `raw/jl_1923_thewashingtontim_122.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/0022225405A/1923122101/0780.xml | 1923 | 200 | 758051 | **含本人直引** |
| 277 | `raw/jl_1923_brownsvilleheral_404.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_burnett_ver01/data/sn86063730/00332893853/1923122701/0397.xml | 1923 | 200 | 1096759 | 纯第三方叙述 |
| 278 | `raw/jl_1923_casperdailytribu_399.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150461/1923122701/0725.xml | 1923 | 200 | 810430 | 纯第三方叙述 |
| 279 | `raw/jl_1924_casperdailytribu_386.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150461/1924010801/0853.xml | 1924 | 200 | 761460 | 纯第三方叙述 |
| 280 | `raw/jl_1924_thebirminghamage_295.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_foster_ver01/data/sn85038485/00513684125/1924010801/0148.xml | 1924 | 200 | 1166969 | 纯第三方叙述 |
| 281 | `raw/jl_1924_themontgomeryadv_267.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_hurston_ver01/data/sn84020645/00517017991/1924010801/0120.xml | 1924 | 200 | 1072763 | 纯第三方叙述 |
| 282 | `raw/jl_1924_themilwaukeelead_471.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_feta_ver01/data/sn83045293/00517012749/1924011001/0216.xml | 1924 | 200 | 1389297 | 纯第三方叙述 |
| 283 | `raw/jl_1924_thewashingtontim_125.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/00222254073/1924011001/0183.xml | 1924 | 200 | 782947 | 纯第三方叙述 |
| 284 | `raw/jl_1924_theindianapolist_485.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348754/1924012501/0271.xml | 1924 | 200 | 1510844 | 纯第三方叙述 |
| 285 | `raw/jl_1924_eaststlouisdaily_384.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_ibis_ver01/data/sn92053739/00529044823/1924020101/0315.xml | 1924 | 200 | 1074506 | 纯第三方叙述 |
| 286 | `raw/jl_1924_theindianapolist_480.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348754/1924020101/0351.xml | 1924 | 200 | 1267788 | 纯第三方叙述 |
| 287 | `raw/jl_1924_casperdailytribu_437.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150473/1924021201/0197.xml | 1924 | 200 | 1023732 | 纯第三方叙述 |
| 288 | `raw/jl_1924_eveningstar_502.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_beiderbecke_ver01/data/sn83045462/00280657475/1924021201/0557.xml | 1924 | 200 | 1408181 | 纯第三方叙述 |
| 289 | `raw/jl_1924_theindianapolist_484.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348754/1924021301/0476.xml | 1924 | 200 | 1523725 | 纯第三方叙述 |
| 290 | `raw/jl_1924_thebeatricedaily_278.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_indigobunting_ver01/data/sn84020107/00517014564/1924021601/0390.xml | 1924 | 200 | 641127 | 纯第三方叙述 |
| 291 | `raw/jl_1924_theseattlestar_284.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_kingfisher_ver02/data/sn87093407/00340585458/1924021601/0447.xml | 1924 | 200 | 1265237 | 纯第三方叙述 |
| 292 | `raw/jl_1924_thewashingtondai_491.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_iooss_ver02/data/sn82016181/00529045669/1924021602/0616.xml | 1924 | 200 | 353164 | 纯第三方叙述 |
| 293 | `raw/jl_1924_themilwaukeelead_438.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_gouda_ver01/data/sn83045293/00517012737/1924021701/0064.xml | 1924 | 200 | 1080493 | 纯第三方叙述 |
| 294 | `raw/jl_1924_thebirminghamage_095.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_foster_ver01/data/sn85038485/00513684125/1924022001/0991.xml | 1924 | 200 | 749790 | 纯第三方叙述 |
| 295 | `raw/jl_1924_casperdailytribu_505.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150473/1924022201/0317.xml | 1924 | 200 | 445708 | **含本人直引** |
| 296 | `raw/jl_1924_thebirminghamage_277.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_foster_ver01/data/sn85038485/00513684137/1924030101/0005.xml | 1924 | 200 | 1140803 | 纯第三方叙述 |
| 297 | `raw/jl_1924_eaststlouisdaily_001.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_junco_ver01/data/sn92053739/00529044859/1924070601/0355.xml | 1924 | 200 | 334096 | 纯第三方叙述 |
| 298 | `raw/jl_1924_eveningstar_055.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_carmichael_ver01/data/sn83045462/00280657578/1924071601/0178.xml | 1924 | 200 | 449278 | 纯第三方叙述 |
| 299 | `raw/jl_1924_themilwaukeelead_239.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_gouda_ver01/data/sn83045293/00517012828/1924071801/0062.xml | 1924 | 200 | 1406175 | 纯第三方叙述 |
| 300 | `raw/jl_1924_eveningstar_148.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_carmichael_ver01/data/sn83045462/00280657785/1924081501/0707.xml | 1924 | 200 | 932564 | 纯第三方叙述 |
| 301 | `raw/jl_1924_themilwaukeelead_418.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_gouda_ver01/data/sn83045293/00517013328/1924110601/0089.xml | 1924 | 200 | 1000589 | 纯第三方叙述 |
| 302 | `raw/jl_1924_eveningstar_429.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_dorsey_ver02/data/sn83045462/00280657724/1924110701/0159.xml | 1924 | 200 | 1253577 | 纯第三方叙述 |
| 303 | `raw/jl_1924_theindependentre_346.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_harpswell_ver01/data/sn96075050/00340587881/1924111301/1286.xml | 1924 | 200 | 1198424 | 纯第三方叙述 |
| 304 | `raw/jl_1924_thebirminghamage_402.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_groom_ver01/data/sn85038485/00513684186/1924113001/0712.xml | 1924 | 200 | 1051389 | 纯第三方叙述 |
| 305 | `raw/jl_1924_southbendnewstim_315.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_data_ver01/data/sn87055779/00517017073/1924120301/0561.xml | 1924 | 200 | 992376 | 纯第三方叙述 |
| 306 | `raw/jl_1925_thewashingtontim_058.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254127/1925011401/0268.xml | 1925 | 200 | 484185 | 纯第三方叙述 |
| 307 | `raw/jl_1925_dailykennebecjou_333.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_hale_ver01/data/sn82014248/00513683297/1925020301/0372.xml | 1925 | 200 | 1657715 | 纯第三方叙述 |
| 308 | `raw/jl_1925_eveningstar_400.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_dorsey_ver02/data/sn83045462/00280657669/1925021101/0315.xml | 1925 | 200 | 931290 | 纯第三方叙述 |
| 309 | `raw/jl_1925_thewashingtontim_132.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254152/1925021101/0174.xml | 1925 | 200 | 821667 | 纯第三方叙述 |
| 310 | `raw/jl_1925_dailykennebecjou_352.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_hale_ver01/data/sn82014248/00513683297/1925022401/0595.xml | 1925 | 200 | 1715550 | 纯第三方叙述 |
| 311 | `raw/jl_1925_thewashingtontim_054.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254164/1925031701/0176.xml | 1925 | 200 | 470417 | 纯第三方叙述 |
| 312 | `raw/jl_1925_newbritainherald_072.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_floyd_ver01/data/sn82014519/00414219147/1925031801/0297.xml | 1925 | 200 | 185457 | 纯第三方叙述 |
| 313 | `raw/jl_1925_thebirminghamage_406.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_julian_ver01/data/sn85038485/00517018259/1925041601/0376.xml | 1925 | 200 | 1093344 | 纯第三方叙述 |
| 314 | `raw/jl_1925_vilascountynews_412.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_lenawee_ver01/data/sn85040613/00514158812/1925042201/0331.xml | 1925 | 200 | 823625 | 纯第三方叙述 |
| 315 | `raw/jl_1925_dailykennebecjou_364.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_hale_ver01/data/sn82014248/00513683315/1925051201/0124.xml | 1925 | 200 | 1428889 | 纯第三方叙述 |
| 316 | `raw/jl_1925_thewashingtontim_144.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254188/1925052801/0460.xml | 1925 | 200 | 839351 | 纯第三方叙述 |
| 317 | `raw/jl_1925_americustimesrec_042.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_eridanus_ver02/data/sn89053204/00393343680/1925090201/0723.xml | 1925 | 200 | 427824 | 纯第三方叙述 |
| 318 | `raw/jl_1925_thewashingtondai_068.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hine_ver02/data/sn82016181/00529045815/1925090201/0007.xml | 1925 | 200 | 470047 | 纯第三方叙述 |
| 319 | `raw/jl_1925_eveningstar_121.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_ellington_ver02/data/sn83045462/00280659289/1925090901/0392.xml | 1925 | 200 | 726308 | 纯第三方叙述 |
| 320 | `raw/jl_1925_eveningstar_022.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_ellington_ver02/data/sn83045462/00280659290/1925091701/0087.xml | 1925 | 200 | 138559 | 纯第三方叙述 |
| 321 | `raw/jl_1925_thewashingtontim_003.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oshima_ver02/data/sn84026749/0022225422A/1925092101/0097.xml | 1925 | 200 | 168811 | 纯第三方叙述 |
| 322 | `raw/jl_1925_thewashingtontim_021.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oshima_ver02/data/sn84026749/0022225422A/1925092401/0179.xml | 1925 | 200 | 144592 | 纯第三方叙述 |
| 323 | `raw/jl_1925_thewashingtontim_149.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oshima_ver02/data/sn84026749/0022225422A/1925101001/0550.xml | 1925 | 200 | 908694 | 纯第三方叙述 |
| 324 | `raw/jl_1925_brownsvilleheral_097.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/00332894390/1925112501/0209.xml | 1925 | 200 | 783071 | 纯第三方叙述 |
| 325 | `raw/jl_1925_sanantoniolight_020.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_aubrey_ver01/data/sn85060004/00517176886/1925112601/0874.xml | 1925 | 200 | 410051 | 纯第三方叙述 |
| 326 | `raw/jl_1925_sanantoniolight_099.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_aubrey_ver01/data/sn85060004/00517176886/1925113001/1050.xml | 1925 | 200 | 880229 | 纯第三方叙述 |
| 327 | `raw/jl_1925_eaststlouisdaily_018.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_junco_ver01/data/sn92053739/00529044963/1925122001/0352.xml | 1925 | 200 | 356531 | 纯第三方叙述 |
| 328 | `raw/jl_1926_themilwaukeelead_449.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_gouda_ver01/data/sn83045293/00542869227/1926013001/0212.xml | 1926 | 200 | 1233580 | 纯第三方叙述 |
| 329 | `raw/jl_1926_eveningstar_462.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fields_ver02/data/sn83045462/0028065937A/1926020301/0455.xml | 1926 | 200 | 1606475 | 纯第三方叙述 |
| 330 | `raw/jl_1926_themilwaukeelead_318.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_havarti_ver01/data/sn83045293/00542869215/1926031701/0172.xml | 1926 | 200 | 1372903 | 纯第三方叙述 |
| 331 | `raw/jl_1926_thebismarcktribu_410.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_denobulan_ver01/data/sn85042243/00199918631/1926051401/0952.xml | 1926 | 200 | 557956 | 纯第三方叙述 |
| 332 | `raw/jl_1926_southbendnewstim_139.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_enterprise_ver01/data/sn87055779/00517016767/1926052901/0614.xml | 1926 | 200 | 383591 | 纯第三方叙述 |
| 333 | `raw/jl_1926_dailykennebecjou_379.txt` | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_iceboro_ver01/data/sn82014248/00513683376/1926062601/0637.xml | 1926 | 200 | 1550869 | 纯第三方叙述 |
| 334 | `raw/jl_1926_eveningstar_092.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_goodman_ver02/data/sn83045462/00280659150/1926102601/0361.xml | 1926 | 200 | 636970 | 纯第三方叙述 |
| 335 | `raw/jl_1926_thewashingtontim_126.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/0022225436A/1926102601/0028.xml | 1926 | 200 | 772204 | 纯第三方叙述 |
| 336 | `raw/jl_1926_eveningstar_124.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_goodman_ver02/data/sn83045462/00280659198/1926121201/0041.xml | 1926 | 200 | 750193 | 纯第三方叙述 |
| 337 | `raw/jl_1926_thewashingtontim_518.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254371/1926121601/0514.xml | 1926 | 200 | 294056 | 纯第三方叙述 |
| 338 | `raw/jl_1927_brownsvilleheral_382.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/00332894766/1927041201/0120.xml | 1927 | 200 | 968588 | 纯第三方叙述 |
| 339 | `raw/jl_1927_newbritainherald_395.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_genesis_ver01/data/sn82014519/00414219755/1927041201/0801.xml | 1927 | 200 | 487810 | 纯第三方叙述 |
| 340 | `raw/jl_1927_eveningstar_046.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hines_ver01/data/sn83045462/00280659733/1927053101/0516.xml | 1927 | 200 | 391493 | 纯第三方叙述 |
| 341 | `raw/jl_1927_thedailyworker_087.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_emerald_ver03/data/sn84020097/00332897792/1927053101/0921.xml | 1927 | 200 | 795563 | 纯第三方叙述 |
| 342 | `raw/jl_1927_eveningstar_066.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_irving_ver01/data/sn83045462/00280659745/1927060701/0203.xml | 1927 | 200 | 497750 | 纯第三方叙述 |
| 343 | `raw/jl_1927_themontgomeryadv_074.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_julian_ver01/data/sn84020645/0051701820A/1927060701/0705.xml | 1927 | 200 | 648013 | 纯第三方叙述 |
| 344 | `raw/jl_1927_thewashingtontim_067.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254425/1927060801/0005.xml | 1927 | 200 | 489397 | 纯第三方叙述 |
| 345 | `raw/jl_1927_brownsvilleheral_038.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/0033289478A/1927061201/0122.xml | 1927 | 200 | 547783 | 纯第三方叙述 |
| 346 | `raw/jl_1927_sewarddailygatew_029.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_icelandgull_ver01/data/sn87062169/00514153929/1927061301/0284.xml | 1927 | 200 | 327167 | 纯第三方叙述 |
| 347 | `raw/jl_1927_thewashingtontim_030.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254425/1927070101/0503.xml | 1927 | 200 | 322531 | 纯第三方叙述 |
| 348 | `raw/jl_1927_thedailyalaskaem_063.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_goshawk_ver01/data/sn83045499/00393342122/1927070701/0462.xml | 1927 | 200 | 430220 | 纯第三方叙述 |
| 349 | `raw/jl_1927_thewashingtondai_084.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_dicorcia_ver01/data/sn82016181/0052904592A/1927070901/0140.xml | 1927 | 200 | 531683 | 纯第三方叙述 |
| 350 | `raw/jl_1927_thedailyworker_075.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_fluorite_ver01/data/sn84020097/00332897603/1927071401/0081.xml | 1927 | 200 | 784780 | 纯第三方叙述 |
| 351 | `raw/jl_1927_eveningstar_145.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_irving_ver01/data/sn83045462/00280659770/1927072101/0374.xml | 1927 | 200 | 887255 | 纯第三方叙述 |
| 352 | `raw/jl_1927_themontgomeryadv_405.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_julian_ver01/data/sn84020645/00517018193/1927072201/0354.xml | 1927 | 200 | 1058321 | 纯第三方叙述 |
| 353 | `raw/jl_1927_thewashingtontim_057.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254425/1927072501/0960.xml | 1927 | 200 | 490336 | 纯第三方叙述 |
| 354 | `raw/jl_1927_brownsvilleheral_103.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/00332894791/1927072801/0280.xml | 1927 | 200 | 830324 | 纯第三方叙述 |
| 355 | `raw/jl_1927_thecordeledispat_093.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/2022239700/00517010418/1927072801/0297.xml | 1927 | 200 | 640958 | 纯第三方叙述 |
| 356 | `raw/jl_1927_thesiftingsheral_062.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_ilmenite_ver01/data/sn91050062/00542869781/1927072801/0281.xml | 1927 | 200 | 456348 | 纯第三方叙述 |
| 357 | `raw/jl_1927_newbritainherald_396.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_genesis_ver01/data/sn82014519/00414219779/1927080901/0653.xml | 1927 | 200 | 513257 | 纯第三方叙述 |
| 358 | `raw/jl_1927_thewestatlanticc_394.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_jackson_ver01/data/sn92059906/00513685920/1927110901/0495.xml | 1927 | 200 | 801984 | 纯第三方叙述 |
| 359 | `raw/jl_1928_eveningstar_112.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_johnson_ver01/data/sn83045462/0028065954A/1928040601/0201.xml | 1928 | 200 | 733923 | 纯第三方叙述 |
| 360 | `raw/jl_1928_thewashingtontim_422.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_quine_ver02/data/sn84026749/00222254516/1928051401/0113.xml | 1928 | 200 | 1188429 | 纯第三方叙述 |
| 361 | `raw/jl_1928_newbritainherald_542.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_hendrix_ver01/data/sn82014519/00414219652/1928110901/0177.xml | 1928 | 200 | 289338 | 纯第三方叙述 |
| 362 | `raw/jl_1928_eveningstar_432.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_keppard_ver01/data/sn83045462/00280600076/1928122301/0141.xml | 1928 | 200 | 1309135 | 纯第三方叙述 |
| 363 | `raw/jl_1928_thewashingtondai_525.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fink_ver02/data/sn82016181/00529046005/1928122801/1202.xml | 1928 | 200 | 383763 | 纯第三方叙述 |
| 364 | `raw/jl_1929_thewashingtontim_497.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_adamsmorgan_ver01/data/sn84026749/00222254589/1929010701/0097.xml | 1929 | 200 | 862646 | 纯第三方叙述 |
| 365 | `raw/jl_1929_newbritainherald_472.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_hendrix_ver01/data/sn82014519/00414219664/1929012401/0417.xml | 1929 | 200 | 1031289 | 纯第三方叙述 |
| 366 | `raw/jl_1929_themilwaukeelead_138.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_italico_ver01/data/sn83045293/00542869148/1929013101/0508.xml | 1929 | 200 | 707035 | 纯第三方叙述 |
| 367 | `raw/jl_1929_brownsvilleheral_101.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_long_ver01/data/sn86063730/00332894262/1929040401/0081.xml | 1929 | 200 | 827375 | 纯第三方叙述 |
| 368 | `raw/jl_1929_brownsvilleheral_417.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_long_ver01/data/sn86063730/00332894262/1929040402/0097.xml | 1929 | 200 | 1154377 | 纯第三方叙述 |
| 369 | `raw/jl_1929_newbritainherald_475.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_hendrix_ver01/data/sn82014519/00414219676/1929040401/0647.xml | 1929 | 200 | 1046183 | 纯第三方叙述 |
| 370 | `raw/jl_1929_themilwaukeelead_089.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_italico_ver01/data/sn83045293/00542869124/1929040501/0027.xml | 1929 | 200 | 581358 | 纯第三方叙述 |
| 371 | `raw/jl_1929_eveningstar_503.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_lateef_ver01/data/sn83045462/00280600167/1929040901/0578.xml | 1929 | 200 | 1674341 | 纯第三方叙述 |
| 372 | `raw/jl_1929_thewashingtontim_532.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_adamsmorgan_ver01/data/sn84026749/00222254607/1929041801/0425.xml | 1929 | 200 | 537688 | 纯第三方叙述 |
| 373 | `raw/jl_1929_thebismarcktribu_319.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_ferengi_ver01/data/sn85042243/00199918734/1929090501/0038.xml | 1929 | 200 | 1307738 | 纯第三方叙述 |
| 374 | `raw/jl_1929_eveningstar_305.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_morton_ver01/data/sn83045462/00280659939/1929090901/0395.xml | 1929 | 200 | 1361063 | 纯第三方叙述 |
| 375 | `raw/jl_1929_brownsvilleheral_280.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_long_ver01/data/sn86063730/00332894134/1929091001/0170.xml | 1929 | 200 | 823625 | 纯第三方叙述 |
| 376 | `raw/jl_1929_eveningstar_482.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_morton_ver01/data/sn83045462/00280659976/1929102201/0054.xml | 1929 | 200 | 2103169 | 纯第三方叙述 |
| 377 | `raw/jl_1929_eveningstar_433.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_morton_ver01/data/sn83045462/00280659976/1929102401/0128.xml | 1929 | 200 | 1267353 | 纯第三方叙述 |
| 378 | `raw/jl_1929_thebismarcktribu_321.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_ferengi_ver01/data/sn85042243/00199918734/1929103001/0560.xml | 1929 | 200 | 1394451 | 纯第三方叙述 |
| 379 | `raw/jl_1929_themilwaukeelead_316.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_italico_ver01/data/sn83045293/00542869264/1929103001/0012.xml | 1929 | 200 | 1205778 | 纯第三方叙述 |
| 380 | `raw/jl_1929_thewashingtontim_530.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_adamsmorgan_ver01/data/sn84026749/00222254656/1929103001/0918.xml | 1929 | 200 | 475175 | 纯第三方叙述 |
| 381 | `raw/jl_1929_springfieldweekl_322.txt` | https://tile.loc.gov/storage-services/service/ndnp/mb/batch_mb_basil_ver01/data/sn83020847/00517171086/1929103101/0604.xml | 1929 | 200 | 1334158 | 纯第三方叙述 |
| 382 | `raw/jl_1929_brownsvilleheral_494.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_evans_ver01/data/sn86063730/0033289416A/1929110402/0077.xml | 1929 | 200 | 724050 | 纯第三方叙述 |
| 383 | `raw/jl_1929_brownsvilleheral_495.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_evans_ver01/data/sn86063730/0033289416A/1929110401/0067.xml | 1929 | 200 | 732489 | 纯第三方叙述 |
| 384 | `raw/jl_1929_richmondplanet_019.txt` | https://tile.loc.gov/storage-services/service/ndnp/vi/batch_vi_jumboshrimp_ver01/data/sn84025841/00414216572/1929111601/0368.xml | 1929 | 200 | 202409 | 纯第三方叙述 |
| 385 | `raw/jl_1929_thecalicorockpro_536.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_chalcopyrite_ver01/data/sn83003534/00516990430/1929112201/1151.xml | 1929 | 200 | 480563 | 纯第三方叙述 |
| 386 | `raw/jl_1929_thebismarcktribu_504.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_ferengi_ver01/data/sn85042243/00199918734/1929122101/1034.xml | 1929 | 200 | 1545584 | 纯第三方叙述 |
| 387 | `raw/jl_1929_theindianapolist_440.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_goldman_ver01/data/sn82015313/00383349229/1929122101/0361.xml | 1929 | 200 | 771514 | 纯第三方叙述 |
| 388 | `raw/jl_1929_thewashingtontim_082.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_adamsmorgan_ver01/data/sn84026749/00222254668/1929122101/1296.xml | 1929 | 200 | 548997 | 纯第三方叙述 |
| 389 | `raw/jl_1930_thewashingtondai_516.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hine_ver02/data/sn82016181/00529046078/1930011501/0294.xml | 1930 | 200 | 133183 | 纯第三方叙述 |
| 390 | `raw/jl_1930_eveningstar_317.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_noone_ver01/data/sn83045462/00280600301/1930040601/0216.xml | 1930 | 200 | 1560827 | 纯第三方叙述 |
| 391 | `raw/jl_1930_eveningstar_275.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_noone_ver01/data/sn83045462/00280600301/1930041101/0439.xml | 1930 | 200 | 1347547 | 纯第三方叙述 |
| 392 | `raw/jl_1930_douglasdailydisp_270.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_iotite_ver01/data/sn84020064/0054286641A/1930061001/0001.xml | 1930 | 200 | 909220 | 纯第三方叙述 |
| 393 | `raw/jl_1930_douglasdailydisp_561.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_iotite_ver01/data/sn84020064/00542866421/1930092401/0004.xml | 1930 | 200 | 943505 | 纯第三方叙述 |
| 394 | `raw/jl_1930_eveningstar_285.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oliver_ver01/data/sn83045462/00280600556/1930111901/0318.xml | 1930 | 200 | 1520335 | 纯第三方叙述 |
| 395 | `raw/jl_1931_eveningstar_274.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_perry_ver01/data/sn83045462/00280600325/1931011001/0312.xml | 1931 | 200 | 1094793 | 纯第三方叙述 |
| 396 | `raw/jl_1931_morgancountydemo_336.txt` | https://tile.loc.gov/storage-services/service/ndnp/ohi/batch_ohi_echinacea_ver01/data/sn87075008/00340580011/1931022601/0608.xml | 1931 | 200 | 926396 | 纯第三方叙述 |
| 397 | `raw/jl_1931_eveningstar_570.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_quinne_ver01/data/sn83045462/00280600477/1931073101/0087.xml | 1931 | 200 | 1497842 | 纯第三方叙述 |
| 398 | `raw/jl_1931_douglasdailydisp_562.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_iotite_ver01/data/sn84020064/00529040131/1931081401/0004.xml | 1931 | 200 | 975249 | 纯第三方叙述 |
| 399 | `raw/jl_1931_thewashingtontim_444.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_chinatown_ver01/data/sn84026749/00205696453/1931102801/1443.xml | 1931 | 200 | 1489370 | 纯第三方叙述 |
| 400 | `raw/jl_1931_theindianapolist_559.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_huxley_ver01/data/sn82015313/00383349370/1931111801/0632.xml | 1931 | 200 | 496037 | 纯第三方叙述 |
| 401 | `raw/jl_1932_eveningstar_271.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1arp_ver01/data/sn83045462/00280601007/1932041801/0548.xml | 1932 | 200 | 1173710 | 纯第三方叙述 |
| 402 | `raw/jl_1932_theindianapolist_302.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_huxley_ver01/data/sn82015313/00383349412/1932041801/0381.xml | 1932 | 200 | 1091551 | 纯第三方叙述 |
| 403 | `raw/jl_1932_eveningstar_460.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1arp_ver01/data/sn83045462/00280601032/1932042701/0252.xml | 1932 | 200 | 1360716 | 纯第三方叙述 |
| 404 | `raw/jl_1932_theindianapolist_466.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_huxley_ver01/data/sn82015313/0038334945A/1932100401/0373.xml | 1932 | 200 | 942245 | 纯第三方叙述 |
| 405 | `raw/jl_1932_theindianapolist_052.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_huxley_ver01/data/sn82015313/0038334945A/1932100501/0390.xml | 1932 | 200 | 747083 | **含本人直引** |
| 406 | `raw/jl_1932_thewashingtontim_083.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_chinatown_ver01/data/sn84026749/00205696519/1932102401/1225.xml | 1932 | 200 | 560464 | 纯第三方叙述 |
| 407 | `raw/jl_1932_douglasdailydisp_413.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_jasper_ver03/data/sn84020064/00529040180/1932102501/0001.xml | 1932 | 200 | 992885 | 纯第三方叙述 |
| 408 | `raw/jl_1932_eveningstar_443.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1bernal_ver01/data/sn83045462/00280600805/1932102501/0644.xml | 1932 | 200 | 1239698 | 纯第三方叙述 |
| 409 | `raw/jl_1932_thedailyalaskaem_077.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_bowheadwhale_ver01/data/sn83045499/00514159646/1932113001/0619.xml | 1932 | 200 | 498796 | 纯第三方叙述 |
| 410 | `raw/jl_1933_thewashingtontim_002.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696544/1933032901/0563.xml | 1933 | 200 | 562996 | 纯第三方叙述 |
| 411 | `raw/jl_1933_douglasdailydisp_262.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_jasper_ver03/data/sn84020064/00529040209/1933041801/0001.xml | 1933 | 200 | 1088929 | 纯第三方叙述 |
| 412 | `raw/jl_1933_thewaterburydemo_375.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_deane_ver01/data/sn82014085/00393347740/1933041901/0647.xml | 1933 | 200 | 1055336 | 纯第三方叙述 |
| 413 | `raw/jl_1933_eveningstar_069.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601287/1933092201/0640.xml | 1933 | 200 | 461474 | 纯第三方叙述 |
| 414 | `raw/jl_1933_thedailyalaskaem_107.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159671/1933092201/0140.xml | 1933 | 200 | 609912 | 纯第三方叙述 |
| 415 | `raw/jl_1933_eveningstar_123.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601317/1933102801/0304.xml | 1933 | 200 | 652923 | 纯第三方叙述 |
| 416 | `raw/jl_1933_thewashingtontim_146.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/0020569657A/1933102801/1509.xml | 1933 | 200 | 855650 | 纯第三方叙述 |
| 417 | `raw/jl_1933_eveningstar_110.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601329/1933111601/0481.xml | 1933 | 200 | 605117 | 纯第三方叙述 |
| 418 | `raw/jl_1933_eveningstar_113.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601329/1933112101/0715.xml | 1933 | 200 | 645325 | 纯第三方叙述 |
| 419 | `raw/jl_1933_thewashingtontim_111.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933121301/1091.xml | 1933 | 200 | 687218 | 纯第三方叙述 |
| 420 | `raw/jl_1933_brownsvilleheral_119.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587467/1933122001/0343.xml | 1933 | 200 | 888846 | 纯第三方叙述 |
| 421 | `raw/jl_1933_eveningstar_421.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601469/1933122001/0189.xml | 1933 | 200 | 1066779 | 纯第三方叙述 |
| 422 | `raw/jl_1933_thedailyalaskaem_116.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159671/1933122001/0743.xml | 1933 | 200 | 647597 | 纯第三方叙述 |
| 423 | `raw/jl_1933_theindianapolist_064.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_ingersoll_ver01/data/sn82015313/00383349576/1933122001/0147.xml | 1933 | 200 | 905740 | 纯第三方叙述 |
| 424 | `raw/jl_1933_thekeywestcitize_115.txt` | https://tile.loc.gov/storage-services/service/ndnp/fu/batch_fu_cicerone_ver01/data/sn83016244/00271760826/1933122001/0377.xml | 1933 | 200 | 673625 | 纯第三方叙述 |
| 425 | `raw/jl_1933_thewashingtontim_004.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933122001/1295.xml | 1933 | 200 | 728439 | 纯第三方叙述 |
| 426 | `raw/jl_1933_thewashingtontim_017.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933122001/1296.xml | 1933 | 200 | 870424 | 纯第三方叙述 |
| 427 | `raw/jl_1933_thewaterburydemo_450.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_deane_ver01/data/sn82014085/00393347788/1933122001/0759.xml | 1933 | 200 | 845746 | 纯第三方叙述 |
| 428 | `raw/jl_1933_brownsvilleheral_120.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587467/1933122102/0373.xml | 1933 | 200 | 905693 | 纯第三方叙述 |
| 429 | `raw/jl_1933_eveningstar_036.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601469/1933122101/0258.xml | 1933 | 200 | 314573 | 纯第三方叙述 |
| 430 | `raw/jl_1933_hendersondailydi_109.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_isner_ver01/data/sn91068401/00332892903/1933122101/0505.xml | 1933 | 200 | 603221 | 纯第三方叙述 |
| 431 | `raw/jl_1933_thedailyworker_407.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_fluorite_ver01/data/sn84020097/00332897421/1933122101/0881.xml | 1933 | 200 | 1183654 | 纯第三方叙述 |
| 432 | `raw/jl_1933_thetimesnews_136.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_endive_ver02/data/sn86063811/00279559526/1933122101/0405.xml | 1933 | 200 | 631565 | 纯第三方叙述 |
| 433 | `raw/jl_1933_thewashingtontim_134.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933122101/1326.xml | 1933 | 200 | 780840 | 纯第三方叙述 |
| 434 | `raw/jl_1933_thenomenugget_032.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_arctictern_ver01/data/sn87062013/00414185691/1933122301/0313.xml | 1933 | 200 | 341680 | 纯第三方叙述 |
| 435 | `raw/jl_1933_thebismarcktribu_439.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_horta_ver01/data/sn85042243/00383346046/1933122801/0902.xml | 1933 | 200 | 705689 | 纯第三方叙述 |
| 436 | `raw/jl_1934_imperialvalleypr_555.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_quailbush_ver02/data/sn92070146/00414188758/1934010401/0913.xml | 1934 | 200 | 499146 | 纯第三方叙述 |
| 437 | `raw/jl_1934_thedailyalaskaem_557.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159683/1934011501/0102.xml | 1934 | 200 | 814222 | 纯第三方叙述 |
| 438 | `raw/jl_1934_thewashingtontim_463.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696593/1934011701/0387.xml | 1934 | 200 | 1637327 | 纯第三方叙述 |
| 439 | `raw/jl_1934_thewashingtontim_509.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696593/1934021701/1157.xml | 1934 | 200 | 374454 | 纯第三方叙述 |
| 440 | `raw/jl_1934_thewashingtontim_526.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696593/1934021701/1156.xml | 1934 | 200 | 408977 | 纯第三方叙述 |
| 441 | `raw/jl_1934_eveningstar_056.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601500/1934030601/0347.xml | 1934 | 200 | 379670 | 纯第三方叙述 |
| 442 | `raw/jl_1934_thebismarcktribu_451.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_horta_ver01/data/sn85042243/00383346058/1934030601/0486.xml | 1934 | 200 | 858796 | 纯第三方叙述 |
| 443 | `raw/jl_1934_thewashingtontim_013.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/0020569660A/1934030601/0119.xml | 1934 | 200 | 688861 | 纯第三方叙述 |
| 444 | `raw/jl_1934_thetimesnews_053.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_endive_ver02/data/sn86063811/00279559538/1934030701/0334.xml | 1934 | 200 | 356139 | 纯第三方叙述 |
| 445 | `raw/jl_1934_sanantoniolight_102.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_falcon_ver01/data/sn85060004/00516994319/1934031001/0274.xml | 1934 | 200 | 908299 | 纯第三方叙述 |
| 446 | `raw/jl_1934_mcallendailymoni_538.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_egret_ver01/data/sn88083718/00340586906/1934032201/0183.xml | 1934 | 200 | 836405 | 纯第三方叙述 |
| 447 | `raw/jl_1934_sanantoniolight_537.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_falcon_ver01/data/sn85060004/00516994319/1934032801/0878.xml | 1934 | 200 | 853769 | 纯第三方叙述 |
| 448 | `raw/jl_1934_sanantoniolight_024.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994320/1934041501/0498.xml | 1934 | 200 | 510871 | 纯第三方叙述 |
| 449 | `raw/jl_1934_sanantoniolight_490.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994320/1934041501/0496.xml | 1934 | 200 | 559969 | 纯第三方叙述 |
| 450 | `raw/jl_1934_sanantoniolight_086.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994320/1934041801/0588.xml | 1934 | 200 | 837933 | **含本人直引** |
| 451 | `raw/jl_1934_thedailyalaskaem_043.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159695/1934052301/0161.xml | 1934 | 200 | 385046 | 纯第三方叙述 |
| 452 | `raw/jl_1934_eveningstar_033.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1ernst_ver01/data/sn83045462/00280601160/1934062801/0370.xml | 1934 | 200 | 306381 | 纯第三方叙述 |
| 453 | `raw/jl_1934_thewashingtontim_034.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/00205696623/1934062801/0760.xml | 1934 | 200 | 332656 | **含本人直引** |
| 454 | `raw/jl_1934_thewashingtontim_551.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/00205696635/1934070501/0078.xml | 1934 | 200 | 795941 | 纯第三方叙述 |
| 455 | `raw/jl_1934_eveningstar_508.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1ernst_ver01/data/sn83045462/00280601160/1934070601/0729.xml | 1934 | 200 | 274901 | 纯第三方叙述 |
| 456 | `raw/jl_1934_brownsvilleheral_553.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587790/1934070902/0202.xml | 1934 | 200 | 952878 | 纯第三方叙述 |
| 457 | `raw/jl_1934_brownsvilleheral_554.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587790/1934070901/0194.xml | 1934 | 200 | 957850 | 纯第三方叙述 |
| 458 | `raw/jl_1934_thewashingtontim_544.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/00205696635/1934071101/0245.xml | 1934 | 200 | 709818 | 纯第三方叙述 |
| 459 | `raw/jl_1934_sanantoniolight_517.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994368/1934082101/0574.xml | 1934 | 200 | 534893 | 纯第三方叙述 |
| 460 | `raw/jl_1934_brownsvilleheral_547.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587819/1934090801/0130.xml | 1934 | 200 | 921289 | 纯第三方叙述 |
| 461 | `raw/jl_1934_theindianapolist_473.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_jillette_ver01/data/sn82015313/00383349655/1934090801/0128.xml | 1934 | 200 | 1034406 | 纯第三方叙述 |
| 462 | `raw/jl_1934_theindianapolist_474.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_jillette_ver01/data/sn82015313/00383349655/1934090802/0146.xml | 1934 | 200 | 1044833 | 纯第三方叙述 |
| 463 | `raw/jl_1934_brownsvilleheral_548.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587819/1934090902/0158.xml | 1934 | 200 | 922170 | 纯第三方叙述 |
| 464 | `raw/jl_1934_brownsvilleheral_549.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587819/1934090901/0142.xml | 1934 | 200 | 918592 | 纯第三方叙述 |
| 465 | `raw/jl_1934_thebismarcktribu_477.txt` | https://tile.loc.gov/storage-services/service/ndnp/ndhi/batch_ndhi_horta_ver01/data/sn85042243/00383346071/1934091301/0091.xml | 1934 | 200 | 1146160 | 纯第三方叙述 |
| 466 | `raw/jl_1934_sanantoniolight_514.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/0051699437A/1934093001/0940.xml | 1934 | 200 | 422126 | 纯第三方叙述 |
| 467 | `raw/jl_1935_eveningstar_147.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1freud_ver01/data/sn83045462/00280601457/1935021701/0455.xml | 1935 | 200 | 817491 | 纯第三方叙述 |
| 468 | `raw/jl_1935_springfieldweekl_250.txt` | https://tile.loc.gov/storage-services/service/ndnp/mb/batch_mb_basil_ver01/data/sn83020847/0051717094A/1935022101/0102.xml | 1935 | 200 | 1438893 | 纯第三方叙述 |
| 469 | `raw/jl_1935_thesaukcentreher_392.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_croquet_ver01/data/sn89064489/00393340356/1935050201/0151.xml | 1935 | 200 | 922808 | 纯第三方叙述 |
| 470 | `raw/jl_1935_thebrooksvillejo_129.txt` | https://tile.loc.gov/storage-services/service/ndnp/fu/batch_fu_jennings_ver01/data/sn95047246/00529042206/1935061301/0589.xml | 1935 | 200 | 690564 | 纯第三方叙述 |
| 471 | `raw/jl_1935_theindianapolist_289.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_jillette_ver01/data/sn82015313/00383349771/1935092401/0243.xml | 1935 | 200 | 968690 | 纯第三方叙述 |
| 472 | `raw/jl_1935_sanantoniolight_202.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994514/1935110301/0140.xml | 1935 | 200 | 497571 | 纯第三方叙述 |
| 473 | `raw/jl_1935_sanantoniolight_209.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994514/1935110301/0140.xml | 1935 | 200 | 497571 | 纯第三方叙述 |
| 474 | `raw/jl_1935_sanantoniolight_027.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994526/1935120101/0050.xml | 1935 | 200 | 624311 | 纯第三方叙述 |
| 475 | `raw/jl_1935_thewashingtontim_007.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120401/0079.xml | 1935 | 200 | 421428 | 纯第三方叙述 |
| 476 | `raw/jl_1935_thewashingtontim_014.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120501/0106.xml | 1935 | 200 | 721238 | 纯第三方叙述 |
| 477 | `raw/jl_1935_thewashingtontim_005.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120601/0165.xml | 1935 | 200 | 349248 | 纯第三方叙述 |
| 478 | `raw/jl_1935_thewashingtondai_051.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mark_ver01/data/sn82016181/00516999494/1935120701/1281.xml | 1935 | 200 | 396757 | 纯第三方叙述 |
| 479 | `raw/jl_1935_thewashingtontim_114.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120701/0205.xml | 1935 | 200 | 718141 | 纯第三方叙述 |
| 480 | `raw/jl_1935_sanantoniolight_006.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994526/1935120801/0248.xml | 1935 | 200 | 931377 | 纯第三方叙述 |
| 481 | `raw/jl_1935_thewashingtontim_065.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935121901/0623.xml | 1935 | 200 | 499873 | 纯第三方叙述 |
| 482 | `raw/jl_1935_imperialvalleypr_385.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_quailbush_ver02/data/sn92070146/00414188795/1935122001/0597.xml | 1935 | 200 | 486577 | 纯第三方叙述 |
| 483 | `raw/jl_1935_thewashingtondai_059.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mark_ver01/data/sn82016181/00516999494/1935122101/1864.xml | 1935 | 200 | 458747 | 纯第三方叙述 |
| 484 | `raw/jl_1935_thewashingtondai_035.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mark_ver01/data/sn82016181/00516999494/1935122501/1979.xml | 1935 | 200 | 351454 | 纯第三方叙述 |
| 485 | `raw/jl_1936_imperialvalleypr_452.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_quailbush_ver02/data/sn92070146/00414188795/1936010301/0668.xml | 1936 | 200 | 849513 | 纯第三方叙述 |
| 486 | `raw/jl_1936_imperialvalleypr_445.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_quailbush_ver02/data/sn92070146/00414188795/1936012601/0833.xml | 1936 | 200 | 808430 | 纯第三方叙述 |
| 487 | `raw/jl_1936_imperialvalleypr_411.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_quailbush_ver02/data/sn92070146/00414188795/1936022701/1086.xml | 1936 | 200 | 595446 | 纯第三方叙述 |
| 488 | `raw/jl_1936_thewashingtontim_507.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698061/1936022801/0738.xml | 1936 | 200 | 261883 | 纯第三方叙述 |
| 489 | `raw/jl_1936_imperialvalleypr_408.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_quailbush_ver02/data/sn92070146/00414188801/1936032601/0151.xml | 1936 | 200 | 551349 | 纯第三方叙述 |
| 490 | `raw/jl_1936_theindianapolist_127.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_kurtz_ver01/data/sn82015313/00383349837/1936032601/0511.xml | 1936 | 200 | 367418 | 纯第三方叙述 |
| 491 | `raw/jl_1936_thewashingtondai_026.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_leibovitz_ver01/data/sn82016181/00516999512/1936032601/0782.xml | 1936 | 200 | 262805 | 纯第三方叙述 |
| 492 | `raw/jl_1936_sanantoniolight_506.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994575/1936052101/0740.xml | 1936 | 200 | 420429 | 纯第三方叙述 |
| 493 | `raw/jl_1937_eveningstar_214.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1johns_ver01/data/sn83045462/00280601901/1937040101/0369.xml | 1937 | 200 | 1041355 | 纯第三方叙述 |
| 494 | `raw/jl_1937_thewashingtontim_071.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hawthorne_ver01/data/sn84026749/0020569819A/1937042901/0890.xml | 1937 | 200 | 525343 | 纯第三方叙述 |
| 495 | `raw/jl_1937_thewashingtontim_045.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hawthorne_ver01/data/sn84026749/0020569819A/1937043001/0955.xml | 1937 | 200 | 366717 | 纯第三方叙述 |
| 496 | `raw/jl_1937_imperialvalleypr_416.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_roseheath_ver01/data/sn92070146/00414188825/1937060301/1206.xml | 1937 | 200 | 613481 | 纯第三方叙述 |
| 497 | `raw/jl_1937_sanantoniolight_098.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_kestrel_ver01/data/sn85060004/00516994708/1937060301/0065.xml | 1937 | 200 | 854334 | 纯第三方叙述 |
| 498 | `raw/jl_1937_thekeywestcitize_389.txt` | https://tile.loc.gov/storage-services/service/ndnp/fu/batch_fu_cicerone_ver01/data/sn83016244/00271761302/1937072801/0092.xml | 1937 | 200 | 798359 | 纯第三方叙述 |
| 499 | `raw/jl_1937_thewaterburydemo_306.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_foulois_ver01/data/sn82014085/00393346942/1937072801/0427.xml | 1937 | 200 | 764947 | 纯第三方叙述 |
| 500 | `raw/jl_1937_thewashingtontim_012.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hawthorne_ver01/data/sn84026749/0020569822A/1937081901/0209.xml | 1937 | 200 | 667378 | 纯第三方叙述 |
| 501 | `raw/jl_1937_thewashingtondai_037.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_bullock_ver01/data/sn82016181/00516999597/1937082001/1446.xml | 1937 | 200 | 325063 | 纯第三方叙述 |
| 502 | `raw/jl_1937_thewaterburydemo_454.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_foulois_ver01/data/sn82014085/00393346942/1937082301/0849.xml | 1937 | 200 | 812924 | 纯第三方叙述 |
| 503 | `raw/jl_1937_sanantoniolight_025.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_kestrel_ver01/data/sn85060004/00516994721/1937082501/0824.xml | 1937 | 200 | 550889 | 纯第三方叙述 |
| 504 | `raw/jl_1937_thewashingtondai_493.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_bullock_ver01/data/sn82016181/00516999615/1937111501/0478.xml | 1937 | 200 | 558100 | 纯第三方叙述 |
| 505 | `raw/jl_1938_thewaterburydemo_345.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_grasso_ver02/data/sn82014085/00393347387/1938041301/0669.xml | 1938 | 200 | 990870 | 纯第三方叙述 |
| 506 | `raw/jl_1938_eveningstar_560.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1miro_ver02/data/sn83045462/00280602280/1938102301/0189.xml | 1938 | 200 | 982008 | 纯第三方叙述 |
| 507 | `raw/jl_1938_hendersondailydi_550.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_jordan_ver01/data/sn91068401/00332892812/1938120101/0436.xml | 1938 | 200 | 684067 | 纯第三方叙述 |
| 508 | `raw/jl_1938_thedailyalaskaem_511.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_herring_ver01/data/sn83045499/00393342365/1938121601/0764.xml | 1938 | 200 | 568315 | 纯第三方叙述 |
| 509 | `raw/jl_1939_thewashingtondai_060.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_kasebier_ver01/data/sn82016181/0051699972A/1939101801/1506.xml | 1939 | 200 | 455709 | 纯第三方叙述 |
| 510 | `raw/jl_1940_eveningstar_543.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1picasso_ver01/data/sn83045462/00280602231/1940050201/0659.xml | 1940 | 200 | 622930 | 纯第三方叙述 |
| 511 | `raw/jl_1940_eveningstar_244.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1picasso_ver01/data/sn83045462/00280602279/1940062001/0439.xml | 1940 | 200 | 1120212 | 纯第三方叙述 |
| 512 | `raw/jl_1940_atlantadailyworl_567.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_dryad_ver03/data/sn82015425/00529040465/1940072401/0150.xml | 1940 | 200 | 1185230 | 纯第三方叙述 |
| 513 | `raw/jl_1940_eveningstar_431.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603016/1940092201/0691.xml | 1940 | 200 | 1197435 | **含本人直引** |
| 514 | `raw/jl_1940_eveningstar_009.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603077/1940112901/0414.xml | 1940 | 200 | 517039 | **含本人直引** |
| 515 | `raw/jl_1940_imperialvalleypr_499.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_roseheath_ver01/data/sn92070146/00414188898/1940112901/0812.xml | 1940 | 200 | 532746 | 纯第三方叙述 |
| 516 | `raw/jl_1940_thewashingtondai_515.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_iturbide_ver01/data/sn82016181/00516999792/1940112901/0985.xml | 1940 | 200 | 130489 | 纯第三方叙述 |
| 517 | `raw/jl_1940_thewaterburydemo_409.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_hepburn_ver01/data/sn82014085/00393347648/1940112901/0452.xml | 1940 | 200 | 517619 | **含本人直引** |
| 518 | `raw/jl_1940_thewilmingtonmor_061.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_fennel_ver02/data/sn78002169/00279559071/1940112901/0378.xml | 1940 | 200 | 412879 | 纯第三方叙述 |
| 519 | `raw/jl_1940_theypsilantidail_558.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_burt_ver03/data/sn97063183/0041418764A/1940112901/0687.xml | 1940 | 200 | 899604 | 纯第三方叙述 |
| 520 | `raw/jl_1940_thewilmingtonmor_563.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_fennel_ver02/data/sn78002169/00279559071/1940120201/0411.xml | 1940 | 200 | 913496 | 纯第三方叙述 |
| 521 | `raw/jl_1940_thewaterburydemo_568.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_hepburn_ver01/data/sn82014085/00393347648/1940120301/0515.xml | 1940 | 200 | 743944 | 纯第三方叙述 |
| 522 | `raw/jl_1940_thelaredotimes_520.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_dove_ver02/data/sn86089568/00517176904/1940120401/0711.xml | 1940 | 200 | 607423 | 纯第三方叙述 |
| 523 | `raw/jl_1940_eveningstar_521.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603089/1940120601/0184.xml | 1940 | 200 | 293500 | 纯第三方叙述 |
| 524 | `raw/jl_1940_thewilmingtonmor_091.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_fennel_ver02/data/sn78002169/00279559071/1940120601/0457.xml | 1940 | 200 | 512705 | 纯第三方叙述 |
| 525 | `raw/jl_1940_askovamerican_566.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_judo_ver02/data/sn89064914/00393341555/1940121201/0423.xml | 1940 | 200 | 1195030 | 纯第三方叙述 |
| 526 | `raw/jl_1941_thekeywestcitize_541.txt` | https://tile.loc.gov/storage-services/service/ndnp/fu/batch_fu_downtown_ver02/data/sn83016244/0041418053A/1941010301/0010.xml | 1941 | 200 | 578462 | 纯第三方叙述 |
| 527 | `raw/jl_1941_brewerygulchgaze_534.txt` | https://tile.loc.gov/storage-services/service/ndnp/az/batch_az_bentonite_ver02/data/sn89070012/00517019550/1941010901/0232.xml | 1941 | 200 | 527827 | 纯第三方叙述 |
| 528 | `raw/jl_1941_thelaredotimes_533.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_dove_ver02/data/sn86089568/00517176916/1941020401/0416.xml | 1941 | 200 | 796670 | 纯第三方叙述 |
| 529 | `raw/jl_1941_imperialvalleypr_564.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_sandwort_ver01/data/sn92070146/00414189003/1941062601/0938.xml | 1941 | 200 | 740538 | 纯第三方叙述 |
| 530 | `raw/jl_1941_auttaja_540.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_jasper_ver01/data/sn93060356/00279552131/1941103001/0586.xml | 1941 | 200 | 612397 | 纯第三方叙述 |
| 531 | `raw/jl_1942_detroiteveningti_094.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_fraser_ver01/data/sn88063294/00414187626/1942012101/0171.xml | 1942 | 200 | 612520 | 纯第三方叙述 |
| 532 | `raw/jl_1942_thewaterburydemo_377.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_ives_ver02/data/sn82014085/00393347144/1942030901/0117.xml | 1942 | 200 | 866475 | 纯第三方叙述 |
| 533 | `raw/jl_1942_imperialvalleypr_427.txt` | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_sandwort_ver01/data/sn92070146/00414189027/1942070201/0527.xml | 1942 | 200 | 715126 | 纯第三方叙述 |
| 534 | `raw/jl_1942_thewaterburydemo_374.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_ives_ver02/data/sn82014085/00393347107/1942112501/0366.xml | 1942 | 200 | 843378 | 纯第三方叙述 |
| 535 | `raw/jl_1943_thewaterburydemo_378.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_johnson_ver01/data/sn82014085/00393347004/1943090701/0081.xml | 1943 | 200 | 983903 | 纯第三方叙述 |
| 536 | `raw/jl_1943_detroiteveningti_513.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_gwinn_ver01/data/sn88063294/00340588605/1943091201/0959.xml | 1943 | 200 | 892093 | 纯第三方叙述 |
| 537 | `raw/jl_1944_detroiteveningti_565.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_holly_ver03/data/sn88063294/00340588708/1944031001/0098.xml | 1944 | 200 | 1238488 | 纯第三方叙述 |
| 538 | `raw/jl_1944_eveningstar_287.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1quidor_ver01/data/sn83045462/00280603685/1944052501/0573.xml | 1944 | 200 | 730064 | 纯第三方叙述 |
| 539 | `raw/jl_1944_theypsilantidail_556.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_burt_ver03/data/sn97063183/00414187730/1944101001/0682.xml | 1944 | 200 | 919855 | 纯第三方叙述 |
| 540 | `raw/jl_1945_thedailymonitorl_590.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_alma_ver01/data/sn96077289/00414187626/1945030801/0429.xml | 1945 | 200 | 512925 | 纯第三方叙述 |
| 541 | `raw/jl_1945_eveningstar_273.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1vuillard_ver01/data/sn83045462/00280604549/1945061301/0084.xml | 1945 | 200 | 397772 | 纯第三方叙述 |
| 542 | `raw/jl_1949_eveningstar_028.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_2isamu_ver01/data/sn83045462/00280605323/1949101401/0203.xml | 1949 | 200 | 259728 | 纯第三方叙述 |
| 543 | `lefevre/lefevre_1923_ReminiscencesOfAStockOperator_gutenberg_60979.txt` | https://www.gutenberg.org/ebooks/60979.txt.utf-8 | 1923 | 200 | 620459 | **Lefèvre（隔离）** |
| 544 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/2022239700/00517010418/1927072501/0275.xml | 1927 | 522 | 0 | 失败：HTTP Error 522: <none> |
| 545 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_rottweiler_ver01/data/sn83045462/00280655557/1903081801/0222.xml | 1903 | 200 | 1597426 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 546 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_holmes_ver01/data/sn89053684/00414182392/1903012501/0292.xml | 1903 | 0 | 0 | 失败：The read operation timed out |
| 547 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_galloway_ver01/data/sn91064030/00513685567/1927110801/0504.xml | 1927 | 0 | 0 | 失败：The read operation timed out |
| 548 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_inxs_ver01/data/sn82014519/00414183517/1929111301/0268.xml | 1929 | 200 | 749699 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 549 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00332894146/1929102501/0516.xml | 1929 | 0 | 0 | 失败：The read operation timed out |
| 550 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_emmett_ver01/data/sn88063294/00414187559/1941120701/0822.xml | 1941 | 200 | 406006 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 551 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1picasso_ver01/data/sn83045462/00280602243/1940050501/0071.xml | 1940 | 200 | 1176682 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 552 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_plymouth_ver01/data/sn90059523/00206537826/1904060701/0102.xml | 1904 | 200 | 1343929 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 553 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_ockham_ver01/data/sn83030193/100481583/1902082201/0940.xml | 1902 | 200 | 735651 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 554 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/vi/batch_vi_teal_ver02/data/sn83045389/00296020114/1915021801/1089.xml | 1915 | 200 | 853624 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 555 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_colfax_ver01/data/sn87055779/00295872044/1915021801/0572.xml | 1915 | 200 | 834974 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 556 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_braniff_ver01/data/sn83045433/00237288543/1915012001/0297.xml | 1915 | 200 | 1156202 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 557 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_quebec_ver03/data/sn84026749/100492222/1904060101/0222.xml | 1904 | 200 | 1127762 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 558 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1picasso_ver01/data/sn83045462/00280602218/1940033101/0397.xml | 1940 | 200 | 1014238 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 559 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_xray_ver02/data/sn84026749/0010049226A/1904062901/0034.xml | 1904 | 200 | 1239451 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 560 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/me/batch_me_eaton_ver01/data/sn82014248/00513682803/1915012001/0232.xml | 1915 | 200 | 1120066 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 561 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_dubliner_ver02/data/sn83045293/00517012968/1916080901/0208.xml | 1916 | 200 | 1245440 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 562 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jacobi_ver01/data/sn82016181/00516999743/1940012401/0652.xml | 1940 | 200 | 461089 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 563 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_italico_ver01/data/sn83045293/00542868818/1928042701/0156.xml | 1928 | 200 | 521068 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 564 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_beatles_ver01/data/sn86069873/00100479308/1905051601/0301.xml | 1905 | 200 | 539493 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 565 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_archylee_ver01/data/sn82016196/00516992323/1943112401/0123.xml | 1943 | 200 | 475816 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 566 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jacobi_ver01/data/sn82016181/00516999755/1940041301/1471.xml | 1940 | 200 | 594421 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 567 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jacobi_ver01/data/sn82016181/00516999755/1940042001/1710.xml | 1940 | 200 | 590696 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 568 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_jacobi_ver01/data/sn82016181/00516999755/1940031301/0414.xml | 1940 | 200 | 571216 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 569 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1miro_ver02/data/sn83045462/00280602280/1938103001/0584.xml | 1938 | 200 | 565539 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 570 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_hodag_ver01/data/sn86086586/00414214460/1902062701/0147.xml | 1902 | 200 | 702027 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 571 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_capa_ver01/data/sn82016181/00516999664/1938101501/1501.xml | 1938 | 200 | 656096 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 572 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_exeter_ver01/data/sn85066387/00175037810/1899021201/0606.xml | 1899 | 200 | 1694674 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 573 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_archylee_ver01/data/sn82016196/00516992347/1944090701/0186.xml | 1944 | 200 | 649844 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 574 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/idhi/batch_idhi_hurston_ver02/data/sn86091109/00295867930/1907102601/0397.xml | 1907 | 200 | 731501 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 575 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_jyme_ver01/data/sn85033133/00514159269/1902062601/0251.xml | 1902 | 200 | 853790 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 576 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_quine_ver02/data/sn84026749/00222254498/1928040501/0612.xml | 1928 | 200 | 969981 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 577 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_russell_ver01/data/sn83030193/175044620/1907050201/0433.xml | 1907 | 200 | 797081 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 578 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_russell_ver01/data/sn83030193/175044656/1907101501/0208.xml | 1907 | 200 | 679485 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 579 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_parkins_ver01/data/sn83030214/00206531861/1915021801/0376.xml | 1915 | 200 | 1068734 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 580 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1noguchi_ver01/data/sn83045462/00280602462/1939072301/0382.xml | 1939 | 200 | 1024158 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 581 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1picasso_ver01/data/sn83045462/00280602188/1940021801/0401.xml | 1940 | 200 | 1016149 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 582 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1oldenburg_ver01/data/sn83045462/00280602097/1939101501/0597.xml | 1939 | 200 | 1062003 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 583 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1oldenburg_ver01/data/sn83045462/00280602103/1939102901/0641.xml | 1939 | 200 | 1070374 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 584 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_dogwood_ver01/data/sn84020358/0027174447A/1906050401/0996.xml | 1906 | 200 | 940098 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 585 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1picasso_ver01/data/sn83045462/00280602231/1940042801/0429.xml | 1940 | 200 | 1120328 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 586 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603065/1940111001/0075.xml | 1940 | 200 | 1122972 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 587 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_quine_ver01/data/sn83030193/175044632/1907091101/0776.xml | 1907 | 200 | 883882 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 588 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/rp/batch_rp_bonedevil_ver01/data/sn91070633/00514153838/1907113001/0893.xml | 1907 | 200 | 1099939 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 589 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1oldenburg_ver01/data/sn83045462/00280602103/1939102201/0231.xml | 1939 | 200 | 1330033 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 590 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_johnson_ver01/data/sn82014085/00393347077/1944120401/0447.xml | 1944 | 200 | 1119472 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 591 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_ahwahnee_ver01/data/sn85066387/00175037792/1898120601/0089.xml | 1898 | 200 | 1254243 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 592 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_japanesechin_ver01/data/sn83045462/0028065534A/1900070701/0083.xml | 1900 | 200 | 1580824 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 593 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/mohi/batch_mohi_ingalls_ver01/data/sn84020274/00294559450/1902020901/0166.xml | 1902 | 200 | 1406849 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 594 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_gleason_ver02/data/sn83030272/00211100096/1915021801/0049.xml | 1915 | 200 | 1484091 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 595 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_horseradish_ver02/data/sn87068097/00383340287/1898121301/0680.xml | 1898 | 200 | 1518324 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 596 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_pound_ver01/data/sn99021999/00280778308/1907120801/0944.xml | 1907 | 200 | 1781087 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 597 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_basenji_ver01/data/sn83045188/print/1906040201/0088.xml | 1906 | 200 | 2036101 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 598 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/nn/batch_nn_hypatia_ver01/data/sn83030272/100481339/1907120801/0617.xml | 1907 | 200 | 3049999 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 599 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/mthi/batch_mthi_jewelwing_ver01/data/sn85053057/00295860248/1899031001/0564.xml | 1899 | 200 | 1132108 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |
| 600 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/curiv/batch_curiv_exeter_ver01/data/sn85066387/00175037822/1899030301/0226.xml | 1899 | 200 | 962926 | 失败：ALTO parsed but 'Livermore' absent (OCR/search mismatch) |

## 六、备注

- **`raw/jl_1940_HowToTradeInStocks_01.txt`**：全书 22,471 词。其中**前言 538 词是第三人 Edward Jerome Dies 写的（署名在文末），必须剔除**；正文 **21,881 词**为 Livermore 第一人称原文（开篇即“Over a long period of years I have rarely attended a dinner party…”）。全书 `Lefevre`／`Livingston` 出现 **0** 次。**版权存疑**：该 IA 副本属 `opensource` 集合、上传者标了 CC public-domain mark，但来源署 “Anna's Archive”，1940 年注册件的美国续期状态**未能独立核实**（Stanford 续期库被 Cloudflare 挡住）。IA 的图书馆副本 `howtotradeinstoc0000live` 为 `access-restricted-item`（仅借阅），未下载。
- **`lefevre/lefevre_1923_…_60979.txt`**：Edwin Lefèvre《Reminiscences of a Stock Operator》，112,180 词，`Livingston` 47 次 / `Livermore` 1 次。**小说，主角 Larry Livingston 是虚构人物**，已隔离，任何一句都不得当作 Livermore 本人的话。
- **误归属实证**：Internet Archive 上有两个条目把这本小说直接题为 “Jesse Livermore Reminiscences Of A Stock Operator”（`jesse-livermore-reminiscences-of-a-stock-operator`、`JesseLivermoreReminiscencesOfAStockOperator`，creator 字段为空）。仅登记，未下载。
- **Project Gutenberg 全库检索**：Lefèvre 在册（#60979，公共领域）；**Livermore 本人 0 条**。
- **署名文章排查**：对全部报纸语料 grep `By Jesse L. Livermore` 命中 6 处，逐条读后**全部是假阳性**（“managed by / statement by / engaged by Jesse L. Livermore”），**未发现任何署名报刊文章**。
- 每份报纸文件的结构：头部元数据 → 自动检出的直引候选 → `LIVERMORE-RELEVANT EXCERPTS`（每处提名前后 ±1500 字符）→ `FULL PAGE OCR`（整版，含同版面无关报道，属正常噪声）。
---

## 七、判断题 A：不经 Lefèvre 转手，他本人的话到底能拿到多少字？

| 来源 | 词数 | 说明 |
|---|---|---|
| 1940《How to Trade in Stocks》正文 | **21,881** | 第一人称原文；已剔除第三人 Edward Jerome Dies 写的 538 词前言 |
| 报纸里人工核实的本人直引（1908–1940，14 份、28 条） | **≈ 620** | 含 1908 棉花、1923 参议院证词、1932/1934 还债、1940-09 最后市场评论、1940-11 遗书 |
| **合计** | **≈ 22,500 词** | |

**结论：约 2.2 万词，且其中 97% 全部压在同一本书上。**
去掉那本书，他一生留下的、可公开抓取的、不经 Lefèvre 转手的原话**只有约 600 词**，散落在 33 年、14 份报纸里。
作为对照：Lefèvre 那本小说是 **112,180 词**——**是他本人全部存世文字的 5 倍**。这就是"Livermore 语录"绝大多数其实出自小说的结构性原因。

## 八、判断题 B：够不够"≥24 份可用源，其中 ≥50% 是一手"？

**先说结论：取决于"一手"怎么定义，两种定义得出相反答案。**

- 定义①「一手 = 同时代原始文献」（报纸原版 OCR 算一手）：
  **541 份报纸 + 1 本书 = 542 份，一手占比 ~100%。远超门槛。**
- 定义②「一手 = 他本人的话」（第三方转述不算）：
  **可用源 = 1 本书 + 14 份含直引的报纸 = 15 份，占 542 份的 2.8%。**
  **≥24 份不达标，≥50% 更是差了一个数量级。**

对人物蒸馏而言，只有定义②有意义——第三方叙述能立事实，立不了人格。**按定义②：不够。**

### 六条泳道逐路给数

| 泳道 | 可用一手源 | 够不够 | 缺口在哪 |
|---|---|---|---|
| `writings` 他写的 | **1**（1940 年那本书，21,881 词）+ 遗书残句 | **严重不足** | 无任何署名文章。已对全部 541 份报纸 grep `By Jesse L. Livermore`，6 处命中全是 "managed by / statement by / engaged by" 的假阳性 |
| `conversations` 访谈对话 | **8**（1908 棉花访谈、1922、1923×2、1924、1932、1934、1940-09） | **勉强，偏薄** | 单条多为 1–3 句，唯一长篇是 1908 与 1940-09 两次；无逐字问答式长访谈可得 |
| `expression` 语言风格 | **1 强 + 620 词碎片** | **单点风险** | 风格样本几乎全来自一本书、一种文体（说教式操作手册），缺口语、缺书信、缺不同场合的语域变化 |
| `external` 他人评述 | **527** | **饱和** | 无缺口，反而需要抽样降噪 |
| `decisions` 具体决策记录 | **充足** | **够** | 1907/1908 棉花与恐慌、1915/1934 破产、1917 还债、1923 参议院证词（Mammoth Oil 池、$9,916 利润为其亲口）、1929、1933、1940 |
| `timeline` 生平事件 | **充足**（1898–1949 逐年覆盖，164 份不同报纸） | **够** | 无缺口 |

**判定：`external`/`decisions`/`timeline` 三路饱和；`writings`/`expression` 两路是硬缺口，`conversations` 勉强。**
瓶颈不是抓取力度，是**史料本身就不存在**——他一生只出过一本书、没写过专栏、没留下可公开的书信集。再加抓 10 倍报纸也只会把 `external` 堆得更高，**不会改变 `writings`/`expression` 的分子**。

### 尚未取到、但确认存在的一手线索（建议后续人工补）

| 线索 | 状态 |
|---|---|
| 1923-12-21 参议院公共土地委员会证词**印本全文**（*Leases upon Naval Oil Reserves* hearings） | 存在但**未取到**：archive.org 无此卷；HathiTrust 被 Cloudflare 挡。这是唯一一份可能提供**数千词逐字问答**的一手材料，价值最高 |
| 1930 年代 Pecora 听证会是否有其证词 | 未核实 |
| FBI Vault（1933 年失踪案由 Bureau of Investigation 介入） | vault.fbi.gov **403 Cloudflare**，未取到 |
| 遗嘱认证／破产法庭卷宗（1915、1934） | 未检索到线上公开全文 |
| 1940 年那本书的**美国版权续期状态** | 未能独立核实（Stanford 续期库被挡） |
