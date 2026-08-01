# HARVEST REPORT — Jesse Lauriston Livermore (1877-11-26 – 1940-11-28)

抓取日期 2026-08-01。表内每一行都来自**实际发生的 HTTP 请求**；未抓到的一律记 failed，无一条凭印象补写。

## 一、六个数字

| | 指标 | 数 |
|---|---|---|
| 1 | 实际抓取成功的文件数 | **150**（149 份报纸整版 OCR + 1 份本人署名专著） |
| 2 | 其中他本人署名（byline 含其名） | **1** —— 仅 1940 年《How to Trade in Stocks》一种 |
| 3 | 含明确归给他的引号直引的文件 / 直引句总条数 | **8 份 / 16 条**（逐条读上下文人工核过） |
| 4 | 纯第三方叙述（无本人直引） | **141** |
| 5 | Lefèvre 及其衍生（单列，不计入可用） | **3** |
| 6 | 失败／OCR 无其名／付费墙 | **1** |

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

## 四、被剔除的误判（自动检测器初筛出但说话人不是他）

- `jl_1922_thethermopolisin_010.txt` — speaker is Rep. Mondell in the Congressional Record, not Livermore
- `jl_1934_eveningstar_056.txt` — speaker is Livermore's lawyer Samuel F. Gillman
- `jl_1933_theindianapolist_064.txt` — speaker is Mrs. Livermore (wife)
- `jl_1933_thewashingtontim_134.txt` — speaker is Mrs. Livermore (wife)
- `jl_1925_thewashingtontim_054.txt` — speaker is Mrs. Livermore (wife)
- `jl_1934_sanantoniolight_086.txt` — one of three flagged quotes is his attorney; another is an unrelated shooting story on the same page
- `jl_1917_newyorktribune_135.txt` — court Q&A about 'J. L. L.' spoken by another witness
- `jl_1935_sanantoniolight_027.txt` — family/doctor dialogue in the Jesse Jr. shooting story

## 五、明细表

| # | 文件名 | URL | 年份 | HTTP | 字节 | 类型 |
|---|---|---|---|---|---|---|
| 1 | `raw/jl_1940_HowToTradeInStocks_01.txt` | https://archive.org/details/how-to-trade-in-stocks-livermore-jesse-l-1940-duell-sloan-pearce-d-8d-4100576687 | 1940 | 200 | 126923 | **本人署名** |
| 2 | `raw/jl_1907_americustimesrec_031.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_ara_ver01/data/sn89053204/00393344350/1907120101/0783.xml | 1907 | 200 | 395363 | 纯第三方叙述 |
| 3 | `raw/jl_1907_themirror_078.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_disco_ver01/data/sn90060762/00199919805/1907121201/0413.xml | 1907 | 200 | 517896 | 纯第三方叙述 |
| 4 | `raw/jl_1907_themirror_079.txt` | https://tile.loc.gov/storage-services/service/ndnp/mnhi/batch_mnhi_disco_ver01/data/sn90060762/00199919805/1907121201/0414.xml | 1907 | 200 | 524955 | 纯第三方叙述 |
| 5 | `raw/jl_1907_thesanantoniolig_118.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_icaria_ver01/data/sn86090330/00517175237/1907121201/0919.xml | 1907 | 200 | 954867 | 纯第三方叙述 |
| 6 | `raw/jl_1907_thecolumbian_128.txt` | https://tile.loc.gov/storage-services/service/ndnp/pst/batch_pst_irvin_ver01/data/sn83032011/00280776890/1907122601/0880.xml | 1907 | 200 | 681209 | 纯第三方叙述 |
| 7 | `raw/jl_1908_theleecountyjour_081.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/sn89053337/00517010431/1908012401/0027.xml | 1908 | 200 | 609641 | 纯第三方叙述 |
| 8 | `raw/jl_1908_thesavannahtribu_108.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_inugami_ver01/data/sn84020323/00517177817/1908012501/0350.xml | 1908 | 200 | 664140 | 纯第三方叙述 |
| 9 | `raw/jl_1908_thewheatlandworl_137.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_aarakocra_ver01/data/sn92066906/0054286218A/1908020701/0898.xml | 1908 | 200 | 657326 | 纯第三方叙述 |
| 10 | `raw/jl_1908_thebirminghamage_011.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_flagg_ver01/data/sn85038485/00340583838/1908080701/0476.xml | 1908 | 200 | 958197 | 纯第三方叙述 |
| 11 | `raw/jl_1908_newyorktribune_049.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_brazil_ver03/data/sn83030214/00175039387/1908081201/0223.xml | 1908 | 200 | 1381691 | 纯第三方叙述 |
| 12 | `raw/jl_1908_theleecountyjour_131.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/sn89053337/00517010431/1908082801/0269.xml | 1908 | 200 | 764415 | 纯第三方叙述 |
| 13 | `raw/jl_1908_newyorktribune_040.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_brazil_ver03/data/sn83030214/00175039399/1908090501/0053.xml | 1908 | 200 | 1341148 | 纯第三方叙述 |
| 14 | `raw/jl_1908_themadisondailyl_140.txt` | https://tile.loc.gov/storage-services/service/ndnp/sdhi/batch_sdhi_grenada_ver01/data/sn99062034/00279523246/1908090501/1208.xml | 1908 | 200 | 629543 | 纯第三方叙述 |
| 15 | `raw/jl_1908_bryanmorningeagl_096.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_infiniti_ver03/data/sn86088652/00200297064/1908090601/0692.xml | 1908 | 200 | 799208 | 纯第三方叙述 |
| 16 | `raw/jl_1909_theeveningstates_076.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_elwha_ver01/data/sn88085421/00237282966/1909050101/0087.xml | 1909 | 200 | 478971 | 纯第三方叙述 |
| 17 | `raw/jl_1909_milfordchronicle_041.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_catwoman_ver01/data/sn87062224/00514156426/1909050701/0168.xml | 1909 | 200 | 431287 | 纯第三方叙述 |
| 18 | `raw/jl_1909_perrysburgjourna_141.txt` | https://tile.loc.gov/storage-services/service/ndnp/ohi/batch_ohi_golf_ver04/data/sn87076843/00237289080/1909081301/0237.xml | 1909 | 200 | 723453 | 纯第三方叙述 |
| 19 | `raw/jl_1909_thespokanepress_088.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_columbia_ver01/data/sn88085947/00211108605/1909081301/0640.xml | 1909 | 200 | 556075 | 纯第三方叙述 |
| 20 | `raw/jl_1909_thespokanepress_090.txt` | https://tile.loc.gov/storage-services/service/ndnp/wa/batch_wa_columbia_ver01/data/sn88085947/00211108605/1909081301/0639.xml | 1909 | 200 | 560172 | 纯第三方叙述 |
| 21 | `raw/jl_1910_thewashingtontim_133.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_whiskey_ver02/data/sn84026749/0010049274A/1910052601/0117.xml | 1910 | 200 | 835794 | 纯第三方叙述 |
| 22 | `raw/jl_1910_thedetroittimes_023.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_gulliver_ver01/data/sn83016689/00279551680/1910082001/0002.xml | 1910 | 200 | 1041663 | **含本人直引** |
| 23 | `raw/jl_1915_thedemocraticadv_047.txt` | https://tile.loc.gov/storage-services/service/ndnp/mdu/batch_mdu_elsberg_ver02/data/sn85038292/00415624153/1915061101/0210.xml | 1915 | 200 | 1298137 | 纯第三方叙述 |
| 24 | `raw/jl_1915_bridgetonpioneer_130.txt` | https://tile.loc.gov/storage-services/service/ndnp/njr/batch_njr_ketchup_ver01/data/sn87068192/00279529777/1915070801/0640.xml | 1915 | 200 | 672013 | 纯第三方叙述 |
| 25 | `raw/jl_1915_eveningstar_044.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_ixtl_ver01/data/sn83045462/0028065873A/1915112801/0046.xml | 1915 | 200 | 301695 | 纯第三方叙述 |
| 26 | `raw/jl_1917_pinebluffdailygr_105.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_kraftwerk_ver01/data/sn89051168/00393343461/1917012501/0463.xml | 1917 | 200 | 573654 | 纯第三方叙述 |
| 27 | `raw/jl_1917_newyorktribune_135.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_thompson_ver02/data/sn83030214/00206532117/1917021601/0315.xml | 1917 | 200 | 734049 | 纯第三方叙述 |
| 28 | `raw/jl_1917_thebirminghamage_073.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_ayler_ver01/data/sn85038485/00340583772/1917021601/0606.xml | 1917 | 200 | 673419 | 纯第三方叙述 |
| 29 | `raw/jl_1917_thebirminghamage_100.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_ayler_ver01/data/sn85038485/00340583772/1917021701/0625.xml | 1917 | 200 | 794921 | 纯第三方叙述 |
| 30 | `raw/jl_1917_arkansasecho_117.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_cosmic_ver01/data/sn88084068/00513688106/1917030101/0229.xml | 1917 | 200 | 720252 | 纯第三方叙述 |
| 31 | `raw/jl_1917_themonitor_015.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_indescribablebeast_ver01/data/00225879/00332899223/1917042801/0882.xml | 1917 | 200 | 272093 | 纯第三方叙述 |
| 32 | `raw/jl_1919_thealaskadailyem_048.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_jellymoss_ver01/data/sn84020657/00279527033/1919012801/0189.xml | 1919 | 200 | 409848 | 纯第三方叙述 |
| 33 | `raw/jl_1919_theandersonnews_104.txt` | https://tile.loc.gov/storage-services/service/ndnp/kyu/batch_kyu_heeler_ver01/data/sn86069242/00516998443/1919020601/0043.xml | 1919 | 200 | 618634 | 纯第三方叙述 |
| 34 | `raw/jl_1922_eveningjournal_142.txt` | https://tile.loc.gov/storage-services/service/ndnp/deu/batch_deu_jimtown_ver01/data/sn85042354/00383342612/1922100901/0029.xml | 1922 | 200 | 852171 | 纯第三方叙述 |
| 35 | `raw/jl_1922_richmondtimesdis_106.txt` | https://tile.loc.gov/storage-services/service/ndnp/vi/batch_vi_xanadu_ver01/data/sn83045389/00296029403/1922100901/0347.xml | 1922 | 200 | 639278 | 纯第三方叙述 |
| 36 | `raw/jl_1922_thethermopolisin_010.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_imp_ver02/data/sn92067173/0051699910A/1922102001/0884.xml | 1922 | 200 | 607015 | 纯第三方叙述 |
| 37 | `raw/jl_1922_thenewyorkherald_070.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eucalyptus_ver01/data/sn83045774/00271744389/1922112601/0866.xml | 1922 | 200 | 535761 | 纯第三方叙述 |
| 38 | `raw/jl_1923_thewashingtontim_016.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/00222253949/1923020501/0471.xml | 1923 | 200 | 783949 | **含本人直引** |
| 39 | `raw/jl_1923_sanantoniolight_050.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_aubrey_ver01/data/sn85060004/00517175973/1923032101/0475.xml | 1923 | 200 | 675178 | 纯第三方叙述 |
| 40 | `raw/jl_1923_theomahamorningb_085.txt` | https://tile.loc.gov/storage-services/service/ndnp/nbu/batch_nbu_haydenstopdog_ver01/data/sn84024326/00332899521/1923032101/0803.xml | 1923 | 200 | 1954429 | 纯第三方叙述 |
| 41 | `raw/jl_1923_thewashingtondai_008.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_fink_ver02/data/sn82016181/00529045621/1923103103/1176.xml | 1923 | 200 | 487499 | 纯第三方叙述 |
| 42 | `raw/jl_1923_eldoradodailynew_080.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_hauerite_ver01/data/sn88084083/00516990648/1923111301/1064.xml | 1923 | 200 | 515302 | **含本人直引** |
| 43 | `raw/jl_1923_theindianapolist_143.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_darrow_ver03/data/sn82015313/00383348742/1923112101/0241.xml | 1923 | 200 | 1401498 | 纯第三方叙述 |
| 44 | `raw/jl_1923_casperdailytribu_039.txt` | https://tile.loc.gov/storage-services/service/ndnp/wyu/batch_wyu_hartville_ver01/data/sn86072160/00514150461/1923122101/0663.xml | 1923 | 200 | 362684 | 纯第三方叙述 |
| 45 | `raw/jl_1923_thewashingtontim_122.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/0022225405A/1923122101/0780.xml | 1923 | 200 | 758051 | **含本人直引** |
| 46 | `raw/jl_1924_thewashingtontim_125.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_melville_ver02/data/sn84026749/00222254073/1924011001/0183.xml | 1924 | 200 | 782947 | 纯第三方叙述 |
| 47 | `raw/jl_1924_thebirminghamage_095.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_foster_ver01/data/sn85038485/00513684125/1924022001/0991.xml | 1924 | 200 | 749790 | 纯第三方叙述 |
| 48 | `raw/jl_1924_eaststlouisdaily_001.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_junco_ver01/data/sn92053739/00529044859/1924070601/0355.xml | 1924 | 200 | 334096 | 纯第三方叙述 |
| 49 | `raw/jl_1924_eveningstar_055.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_carmichael_ver01/data/sn83045462/00280657578/1924071601/0178.xml | 1924 | 200 | 449278 | 纯第三方叙述 |
| 50 | `raw/jl_1924_eveningstar_148.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_carmichael_ver01/data/sn83045462/00280657785/1924081501/0707.xml | 1924 | 200 | 932564 | 纯第三方叙述 |
| 51 | `raw/jl_1925_thewashingtontim_058.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254127/1925011401/0268.xml | 1925 | 200 | 484185 | 纯第三方叙述 |
| 52 | `raw/jl_1925_thewashingtontim_132.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254152/1925021101/0174.xml | 1925 | 200 | 821667 | 纯第三方叙述 |
| 53 | `raw/jl_1925_thewashingtontim_054.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254164/1925031701/0176.xml | 1925 | 200 | 470417 | 纯第三方叙述 |
| 54 | `raw/jl_1925_newbritainherald_072.txt` | https://tile.loc.gov/storage-services/service/ndnp/ct/batch_ct_floyd_ver01/data/sn82014519/00414219147/1925031801/0297.xml | 1925 | 200 | 185457 | 纯第三方叙述 |
| 55 | `raw/jl_1925_thewashingtontim_144.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_nichols_ver02/data/sn84026749/00222254188/1925052801/0460.xml | 1925 | 200 | 839351 | 纯第三方叙述 |
| 56 | `raw/jl_1925_americustimesrec_042.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_eridanus_ver02/data/sn89053204/00393343680/1925090201/0723.xml | 1925 | 200 | 427824 | 纯第三方叙述 |
| 57 | `raw/jl_1925_thewashingtondai_068.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hine_ver02/data/sn82016181/00529045815/1925090201/0007.xml | 1925 | 200 | 470047 | 纯第三方叙述 |
| 58 | `raw/jl_1925_eveningstar_121.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_ellington_ver02/data/sn83045462/00280659289/1925090901/0392.xml | 1925 | 200 | 726308 | 纯第三方叙述 |
| 59 | `raw/jl_1925_eveningstar_022.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_ellington_ver02/data/sn83045462/00280659290/1925091701/0087.xml | 1925 | 200 | 138559 | 纯第三方叙述 |
| 60 | `raw/jl_1925_thewashingtontim_003.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oshima_ver02/data/sn84026749/0022225422A/1925092101/0097.xml | 1925 | 200 | 168811 | 纯第三方叙述 |
| 61 | `raw/jl_1925_thewashingtontim_021.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oshima_ver02/data/sn84026749/0022225422A/1925092401/0179.xml | 1925 | 200 | 144592 | 纯第三方叙述 |
| 62 | `raw/jl_1925_thewashingtontim_149.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_oshima_ver02/data/sn84026749/0022225422A/1925101001/0550.xml | 1925 | 200 | 908694 | 纯第三方叙述 |
| 63 | `raw/jl_1925_brownsvilleheral_097.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/00332894390/1925112501/0209.xml | 1925 | 200 | 783071 | 纯第三方叙述 |
| 64 | `raw/jl_1925_sanantoniolight_020.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_aubrey_ver01/data/sn85060004/00517176886/1925112601/0874.xml | 1925 | 200 | 410051 | 纯第三方叙述 |
| 65 | `raw/jl_1925_sanantoniolight_099.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_aubrey_ver01/data/sn85060004/00517176886/1925113001/1050.xml | 1925 | 200 | 880229 | 纯第三方叙述 |
| 66 | `raw/jl_1925_eaststlouisdaily_018.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_junco_ver01/data/sn92053739/00529044963/1925122001/0352.xml | 1925 | 200 | 356531 | 纯第三方叙述 |
| 67 | `raw/jl_1926_southbendnewstim_139.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_enterprise_ver01/data/sn87055779/00517016767/1926052901/0614.xml | 1926 | 200 | 383591 | 纯第三方叙述 |
| 68 | `raw/jl_1926_eveningstar_092.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_goodman_ver02/data/sn83045462/00280659150/1926102601/0361.xml | 1926 | 200 | 636970 | 纯第三方叙述 |
| 69 | `raw/jl_1926_thewashingtontim_126.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/0022225436A/1926102601/0028.xml | 1926 | 200 | 772204 | 纯第三方叙述 |
| 70 | `raw/jl_1926_eveningstar_124.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_goodman_ver02/data/sn83045462/00280659198/1926121201/0041.xml | 1926 | 200 | 750193 | 纯第三方叙述 |
| 71 | `raw/jl_1927_eveningstar_046.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hines_ver01/data/sn83045462/00280659733/1927053101/0516.xml | 1927 | 200 | 391493 | 纯第三方叙述 |
| 72 | `raw/jl_1927_thedailyworker_087.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_emerald_ver03/data/sn84020097/00332897792/1927053101/0921.xml | 1927 | 200 | 795563 | 纯第三方叙述 |
| 73 | `raw/jl_1927_eveningstar_066.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_irving_ver01/data/sn83045462/00280659745/1927060701/0203.xml | 1927 | 200 | 497750 | 纯第三方叙述 |
| 74 | `raw/jl_1927_themontgomeryadv_074.txt` | https://tile.loc.gov/storage-services/service/ndnp/au/batch_au_julian_ver01/data/sn84020645/0051701820A/1927060701/0705.xml | 1927 | 200 | 648013 | 纯第三方叙述 |
| 75 | `raw/jl_1927_thewashingtontim_067.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254425/1927060801/0005.xml | 1927 | 200 | 489397 | 纯第三方叙述 |
| 76 | `raw/jl_1927_brownsvilleheral_038.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/0033289478A/1927061201/0122.xml | 1927 | 200 | 547783 | 纯第三方叙述 |
| 77 | `raw/jl_1927_sewarddailygatew_029.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_icelandgull_ver01/data/sn87062169/00514153929/1927061301/0284.xml | 1927 | 200 | 327167 | 纯第三方叙述 |
| 78 | `raw/jl_1927_thewashingtontim_030.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254425/1927070101/0503.xml | 1927 | 200 | 322531 | 纯第三方叙述 |
| 79 | `raw/jl_1927_thedailyalaskaem_063.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_goshawk_ver01/data/sn83045499/00393342122/1927070701/0462.xml | 1927 | 200 | 430220 | 纯第三方叙述 |
| 80 | `raw/jl_1927_thewashingtondai_084.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_dicorcia_ver01/data/sn82016181/0052904592A/1927070901/0140.xml | 1927 | 200 | 531683 | 纯第三方叙述 |
| 81 | `raw/jl_1927_thedailyworker_075.txt` | https://tile.loc.gov/storage-services/service/ndnp/iune/batch_iune_fluorite_ver01/data/sn84020097/00332897603/1927071401/0081.xml | 1927 | 200 | 784780 | 纯第三方叙述 |
| 82 | `raw/jl_1927_eveningstar_145.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_irving_ver01/data/sn83045462/00280659770/1927072101/0374.xml | 1927 | 200 | 887255 | 纯第三方叙述 |
| 83 | `raw/jl_1927_thewashingtontim_057.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_pakula_ver02/data/sn84026749/00222254425/1927072501/0960.xml | 1927 | 200 | 490336 | 纯第三方叙述 |
| 84 | `raw/jl_1927_brownsvilleheral_103.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_coleman_ver02/data/sn86063730/00332894791/1927072801/0280.xml | 1927 | 200 | 830324 | 纯第三方叙述 |
| 85 | `raw/jl_1927_thecordeledispat_093.txt` | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/2022239700/00517010418/1927072801/0297.xml | 1927 | 200 | 640958 | 纯第三方叙述 |
| 86 | `raw/jl_1927_thesiftingsheral_062.txt` | https://tile.loc.gov/storage-services/service/ndnp/arhi/batch_arhi_ilmenite_ver01/data/sn91050062/00542869781/1927072801/0281.xml | 1927 | 200 | 456348 | 纯第三方叙述 |
| 87 | `raw/jl_1928_eveningstar_112.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_johnson_ver01/data/sn83045462/0028065954A/1928040601/0201.xml | 1928 | 200 | 733923 | 纯第三方叙述 |
| 88 | `raw/jl_1929_themilwaukeelead_138.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_italico_ver01/data/sn83045293/00542869148/1929013101/0508.xml | 1929 | 200 | 707035 | 纯第三方叙述 |
| 89 | `raw/jl_1929_brownsvilleheral_101.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_long_ver01/data/sn86063730/00332894262/1929040401/0081.xml | 1929 | 200 | 827375 | 纯第三方叙述 |
| 90 | `raw/jl_1929_themilwaukeelead_089.txt` | https://tile.loc.gov/storage-services/service/ndnp/whi/batch_whi_italico_ver01/data/sn83045293/00542869124/1929040501/0027.xml | 1929 | 200 | 581358 | 纯第三方叙述 |
| 91 | `raw/jl_1929_richmondplanet_019.txt` | https://tile.loc.gov/storage-services/service/ndnp/vi/batch_vi_jumboshrimp_ver01/data/sn84025841/00414216572/1929111601/0368.xml | 1929 | 200 | 202409 | 纯第三方叙述 |
| 92 | `raw/jl_1929_thewashingtontim_082.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_adamsmorgan_ver01/data/sn84026749/00222254668/1929122101/1296.xml | 1929 | 200 | 548997 | 纯第三方叙述 |
| 93 | `raw/jl_1932_theindianapolist_052.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_huxley_ver01/data/sn82015313/0038334945A/1932100501/0390.xml | 1932 | 200 | 747083 | **含本人直引** |
| 94 | `raw/jl_1932_thewashingtontim_083.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_chinatown_ver01/data/sn84026749/00205696519/1932102401/1225.xml | 1932 | 200 | 560464 | 纯第三方叙述 |
| 95 | `raw/jl_1932_thedailyalaskaem_077.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_bowheadwhale_ver01/data/sn83045499/00514159646/1932113001/0619.xml | 1932 | 200 | 498796 | 纯第三方叙述 |
| 96 | `raw/jl_1933_thewashingtontim_002.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696544/1933032901/0563.xml | 1933 | 200 | 562996 | 纯第三方叙述 |
| 97 | `raw/jl_1933_eveningstar_069.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601287/1933092201/0640.xml | 1933 | 200 | 461474 | 纯第三方叙述 |
| 98 | `raw/jl_1933_thedailyalaskaem_107.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159671/1933092201/0140.xml | 1933 | 200 | 609912 | 纯第三方叙述 |
| 99 | `raw/jl_1933_eveningstar_123.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601317/1933102801/0304.xml | 1933 | 200 | 652923 | 纯第三方叙述 |
| 100 | `raw/jl_1933_thewashingtontim_146.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/0020569657A/1933102801/1509.xml | 1933 | 200 | 855650 | 纯第三方叙述 |
| 101 | `raw/jl_1933_eveningstar_110.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601329/1933111601/0481.xml | 1933 | 200 | 605117 | 纯第三方叙述 |
| 102 | `raw/jl_1933_eveningstar_113.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601329/1933112101/0715.xml | 1933 | 200 | 645325 | 纯第三方叙述 |
| 103 | `raw/jl_1933_thewashingtontim_111.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933121301/1091.xml | 1933 | 200 | 687218 | 纯第三方叙述 |
| 104 | `raw/jl_1933_brownsvilleheral_119.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587467/1933122001/0343.xml | 1933 | 200 | 888846 | 纯第三方叙述 |
| 105 | `raw/jl_1933_thedailyalaskaem_116.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159671/1933122001/0743.xml | 1933 | 200 | 647597 | 纯第三方叙述 |
| 106 | `raw/jl_1933_theindianapolist_064.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_ingersoll_ver01/data/sn82015313/00383349576/1933122001/0147.xml | 1933 | 200 | 905740 | 纯第三方叙述 |
| 107 | `raw/jl_1933_thekeywestcitize_115.txt` | https://tile.loc.gov/storage-services/service/ndnp/fu/batch_fu_cicerone_ver01/data/sn83016244/00271760826/1933122001/0377.xml | 1933 | 200 | 673625 | 纯第三方叙述 |
| 108 | `raw/jl_1933_thewashingtontim_004.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933122001/1295.xml | 1933 | 200 | 728439 | 纯第三方叙述 |
| 109 | `raw/jl_1933_thewashingtontim_017.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933122001/1296.xml | 1933 | 200 | 870424 | 纯第三方叙述 |
| 110 | `raw/jl_1933_brownsvilleheral_120.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gomez_ver01/data/sn86063730/00340587467/1933122102/0373.xml | 1933 | 200 | 905693 | 纯第三方叙述 |
| 111 | `raw/jl_1933_eveningstar_036.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601469/1933122101/0258.xml | 1933 | 200 | 314573 | 纯第三方叙述 |
| 112 | `raw/jl_1933_hendersondailydi_109.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_isner_ver01/data/sn91068401/00332892903/1933122101/0505.xml | 1933 | 200 | 603221 | 纯第三方叙述 |
| 113 | `raw/jl_1933_thetimesnews_136.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_endive_ver02/data/sn86063811/00279559526/1933122101/0405.xml | 1933 | 200 | 631565 | 纯第三方叙述 |
| 114 | `raw/jl_1933_thewashingtontim_134.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_deanwood_ver01/data/sn84026749/00205696581/1933122101/1326.xml | 1933 | 200 | 780840 | 纯第三方叙述 |
| 115 | `raw/jl_1933_thenomenugget_032.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_arctictern_ver01/data/sn87062013/00414185691/1933122301/0313.xml | 1933 | 200 | 341680 | 纯第三方叙述 |
| 116 | `raw/jl_1934_eveningstar_056.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1duchamp_ver01/data/sn83045462/00280601500/1934030601/0347.xml | 1934 | 200 | 379670 | 纯第三方叙述 |
| 117 | `raw/jl_1934_thewashingtontim_013.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/0020569660A/1934030601/0119.xml | 1934 | 200 | 688861 | 纯第三方叙述 |
| 118 | `raw/jl_1934_thetimesnews_053.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_endive_ver02/data/sn86063811/00279559538/1934030701/0334.xml | 1934 | 200 | 356139 | 纯第三方叙述 |
| 119 | `raw/jl_1934_sanantoniolight_102.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_falcon_ver01/data/sn85060004/00516994319/1934031001/0274.xml | 1934 | 200 | 908299 | 纯第三方叙述 |
| 120 | `raw/jl_1934_sanantoniolight_024.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994320/1934041501/0498.xml | 1934 | 200 | 510871 | 纯第三方叙述 |
| 121 | `raw/jl_1934_sanantoniolight_086.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_gull_ver01/data/sn85060004/00516994320/1934041801/0588.xml | 1934 | 200 | 837933 | **含本人直引** |
| 122 | `raw/jl_1934_thedailyalaskaem_043.txt` | https://tile.loc.gov/storage-services/service/ndnp/ak/batch_ak_commonraven_ver01/data/sn83045499/00514159695/1934052301/0161.xml | 1934 | 200 | 385046 | 纯第三方叙述 |
| 123 | `raw/jl_1934_eveningstar_033.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1ernst_ver01/data/sn83045462/00280601160/1934062801/0370.xml | 1934 | 200 | 306381 | 纯第三方叙述 |
| 124 | `raw/jl_1934_thewashingtontim_034.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_eckington_ver01/data/sn84026749/00205696623/1934062801/0760.xml | 1934 | 200 | 332656 | **含本人直引** |
| 125 | `raw/jl_1935_eveningstar_147.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1freud_ver01/data/sn83045462/00280601457/1935021701/0455.xml | 1935 | 200 | 817491 | 纯第三方叙述 |
| 126 | `raw/jl_1935_thebrooksvillejo_129.txt` | https://tile.loc.gov/storage-services/service/ndnp/fu/batch_fu_jennings_ver01/data/sn95047246/00529042206/1935061301/0589.xml | 1935 | 200 | 690564 | 纯第三方叙述 |
| 127 | `raw/jl_1935_sanantoniolight_027.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994526/1935120101/0050.xml | 1935 | 200 | 624311 | 纯第三方叙述 |
| 128 | `raw/jl_1935_thewashingtontim_007.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120401/0079.xml | 1935 | 200 | 421428 | 纯第三方叙述 |
| 129 | `raw/jl_1935_thewashingtontim_014.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120501/0106.xml | 1935 | 200 | 721238 | 纯第三方叙述 |
| 130 | `raw/jl_1935_thewashingtontim_005.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120601/0165.xml | 1935 | 200 | 349248 | 纯第三方叙述 |
| 131 | `raw/jl_1935_thewashingtondai_051.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mark_ver01/data/sn82016181/00516999494/1935120701/1281.xml | 1935 | 200 | 396757 | 纯第三方叙述 |
| 132 | `raw/jl_1935_thewashingtontim_114.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935120701/0205.xml | 1935 | 200 | 718141 | 纯第三方叙述 |
| 133 | `raw/jl_1935_sanantoniolight_006.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_ibis_ver01/data/sn85060004/00516994526/1935120801/0248.xml | 1935 | 200 | 931377 | 纯第三方叙述 |
| 134 | `raw/jl_1935_thewashingtontim_065.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_foxhall_ver03/data/sn84026749/00205698048/1935121901/0623.xml | 1935 | 200 | 499873 | 纯第三方叙述 |
| 135 | `raw/jl_1935_thewashingtondai_059.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mark_ver01/data/sn82016181/00516999494/1935122101/1864.xml | 1935 | 200 | 458747 | 纯第三方叙述 |
| 136 | `raw/jl_1935_thewashingtondai_035.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_mark_ver01/data/sn82016181/00516999494/1935122501/1979.xml | 1935 | 200 | 351454 | 纯第三方叙述 |
| 137 | `raw/jl_1936_theindianapolist_127.txt` | https://tile.loc.gov/storage-services/service/ndnp/in/batch_in_kurtz_ver01/data/sn82015313/00383349837/1936032601/0511.xml | 1936 | 200 | 367418 | 纯第三方叙述 |
| 138 | `raw/jl_1936_thewashingtondai_026.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_leibovitz_ver01/data/sn82016181/00516999512/1936032601/0782.xml | 1936 | 200 | 262805 | 纯第三方叙述 |
| 139 | `raw/jl_1937_thewashingtontim_071.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hawthorne_ver01/data/sn84026749/0020569819A/1937042901/0890.xml | 1937 | 200 | 525343 | 纯第三方叙述 |
| 140 | `raw/jl_1937_thewashingtontim_045.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hawthorne_ver01/data/sn84026749/0020569819A/1937043001/0955.xml | 1937 | 200 | 366717 | 纯第三方叙述 |
| 141 | `raw/jl_1937_sanantoniolight_098.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_kestrel_ver01/data/sn85060004/00516994708/1937060301/0065.xml | 1937 | 200 | 854334 | 纯第三方叙述 |
| 142 | `raw/jl_1937_thewashingtontim_012.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_hawthorne_ver01/data/sn84026749/0020569822A/1937081901/0209.xml | 1937 | 200 | 667378 | 纯第三方叙述 |
| 143 | `raw/jl_1937_thewashingtondai_037.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_bullock_ver01/data/sn82016181/00516999597/1937082001/1446.xml | 1937 | 200 | 325063 | 纯第三方叙述 |
| 144 | `raw/jl_1937_sanantoniolight_025.txt` | https://tile.loc.gov/storage-services/service/ndnp/txdn/batch_txdn_kestrel_ver01/data/sn85060004/00516994721/1937082501/0824.xml | 1937 | 200 | 550889 | 纯第三方叙述 |
| 145 | `raw/jl_1939_thewashingtondai_060.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_kasebier_ver01/data/sn82016181/0051699972A/1939101801/1506.xml | 1939 | 200 | 455709 | 纯第三方叙述 |
| 146 | `raw/jl_1940_eveningstar_009.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_1rothko_ver02/data/sn83045462/00280603077/1940112901/0414.xml | 1940 | 200 | 517039 | **含本人直引** |
| 147 | `raw/jl_1940_thewilmingtonmor_061.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_fennel_ver02/data/sn78002169/00279559071/1940112901/0378.xml | 1940 | 200 | 412879 | 纯第三方叙述 |
| 148 | `raw/jl_1940_thewilmingtonmor_091.txt` | https://tile.loc.gov/storage-services/service/ndnp/ncu/batch_ncu_fennel_ver02/data/sn78002169/00279559071/1940120601/0457.xml | 1940 | 200 | 512705 | 纯第三方叙述 |
| 149 | `raw/jl_1942_detroiteveningti_094.txt` | https://tile.loc.gov/storage-services/service/ndnp/mimtptc/batch_mimtptc_fraser_ver01/data/sn88063294/00414187626/1942012101/0171.xml | 1942 | 200 | 612520 | 纯第三方叙述 |
| 150 | `raw/jl_1949_eveningstar_028.txt` | https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_dlc_2isamu_ver01/data/sn83045462/00280605323/1949101401/0203.xml | 1949 | 200 | 259728 | 纯第三方叙述 |
| 151 | `lefevre/lefevre_1923_ReminiscencesOfAStockOperator_gutenberg_60979.txt` | https://www.gutenberg.org/ebooks/60979.txt.utf-8 | 1923 | 200 | 620459 | **Lefèvre（隔离）** |
| 152 | (未保存) | https://tile.loc.gov/storage-services/service/ndnp/gu/batch_gu_henson_ver02/data/2022239700/00517010418/1927072501/0275.xml | 1927 | 522 | 0 | 失败：HTTP Error 522: <none> |

## 六、备注

- **`raw/jl_1940_HowToTradeInStocks_01.txt`**：全书 22,471 词。其中**前言 538 词是第三人 Edward Jerome Dies 写的（署名在文末），必须剔除**；正文 **21,881 词**为 Livermore 第一人称原文（开篇即“Over a long period of years I have rarely attended a dinner party…”）。全书 `Lefevre`／`Livingston` 出现 **0** 次。**版权存疑**：该 IA 副本属 `opensource` 集合、上传者标了 CC public-domain mark，但来源署 “Anna's Archive”，1940 年注册件的美国续期状态**未能独立核实**（Stanford 续期库被 Cloudflare 挡住）。IA 的图书馆副本 `howtotradeinstoc0000live` 为 `access-restricted-item`（仅借阅），未下载。
- **`lefevre/lefevre_1923_…_60979.txt`**：Edwin Lefèvre《Reminiscences of a Stock Operator》，112,180 词，`Livingston` 47 次 / `Livermore` 1 次。**小说，主角 Larry Livingston 是虚构人物**，已隔离，任何一句都不得当作 Livermore 本人的话。
- **误归属实证**：Internet Archive 上有两个条目把这本小说直接题为 “Jesse Livermore Reminiscences Of A Stock Operator”（`jesse-livermore-reminiscences-of-a-stock-operator`、`JesseLivermoreReminiscencesOfAStockOperator`，creator 字段为空）。仅登记，未下载。
- **Project Gutenberg 全库检索**：Lefèvre 在册（#60979，公共领域）；**Livermore 本人 0 条**。
- **署名文章排查**：对全部报纸语料 grep `By Jesse L. Livermore` 命中 6 处，逐条读后**全部是假阳性**（“managed by / statement by / engaged by Jesse L. Livermore”），**未发现任何署名报刊文章**。
- 每份报纸文件的结构：头部元数据 → 自动检出的直引候选 → `LIVERMORE-RELEVANT EXCERPTS`（每处提名前后 ±1500 字符）→ `FULL PAGE OCR`（整版，含同版面无关报道，属正常噪声）。