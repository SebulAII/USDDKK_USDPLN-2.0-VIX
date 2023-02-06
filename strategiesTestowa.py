import backtrader
import numpy as np
import statistics as stats


class TestStrategy(backtrader.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    # Mateusz: Dodałem alpha do innitu.
    def __init__(self, alpha, open_threshold, close_threshold, pip_av_days, n_days, max_module_period, min_swap, av_VIX_days, open_VIX, close_vix):
        self.dataclose = self.datas[0].close
        self.order = None
        self.volume = 100000
        # zmienne do ustalenia wielkości pozycji
        self.pip_av_days = pip_av_days   #zmienna 30                                                                 # DO OPTYMALIZACJI
        # zmienne sterujące sygnałem otwarcia/zamknięcia    
        self.alpha = alpha         #domyślne 0.02                                                                 # DO OPTYMALIZACJI    
        self.open_threshold = open_threshold     #domyslne 0.9                                                       
        self.close_threshold = close_threshold   #domyślne 1.2                                                     
        self.n_days = n_days #okres do średniej zmienności w pipsach (z modułów zmienności dziennej)    # DO OPTYMALIZACJI
        self.min_swap = min_swap
        #lists
        #self.zmiana_w_pipsach_1 = []
        #self.zmiana_w_pipsach_2 = []
        self.zmiana_w_pipsach_1_wersja2 = []
        self.zmiana_w_pipsach_2_wersja2 = []
        #self.zmiennosc = []
        self.es_volatility = []
        self.differencePips = []
        self.ticket = None
        self.ES_zmiany = []
        self.warmup = 42
        self.max_module_period = max_module_period
        #self.profit = []
        self.holdingDateList = []
        #self.dailyP_L_change = []
        #self.value_USD_list = []
        #self.returns = []
        self.pair1PriceChange = []
        self.pair2PriceChange = []

        #Pair1ExposureList = []
        #Pair2ExposureList = []

        self.pair1_carry = []
        self.pair2_carry = []

        self.test_daily_change = []
        self.test_daily_change_summary = []

        self.av_VIX_days = av_VIX_days 
        self.av_VIX_list = []
        self.open_VIX = open_VIX
        self.close_vix = close_vix

        self.test_swap_priceChange = 0

    def next(self):
        print(len(self))


        if len(self) >2:

            #wygładzanie wersja 2.0 / zmiana dzienności o 1 do góry potrzebne do kolumny BJ
            self.zmiana_w_pipsach_1_wersja2.append(abs((self.datas[0].close[-1] - self.datas[0].close[-2]) * 10000)) #AW    OK
            self.zmiana_w_pipsach_2_wersja2.append(abs((self.datas[1].close[-1] - self.datas[1].close[-2]) * 10000)) #AX    OK

            self.Pair1_price        = self.datas[0].close[0]
            self.Pair2_price        = self.datas[1].close[0]
            self.Pair1_swap_long    = self.datas[2].close[0]
            self.Pair2_swap_long    = self.datas[3].close[0]
            self.Pair1_swap_short   = self.datas[4].close[0]
            self.Pair2_swap_short   = self.datas[5].close[0]
            self.VIX                = self.datas[6].close[0]

            self.av_VIX_list.append(self.VIX)
            self.av_VIX = np.mean(self.av_VIX_list[:self.av_VIX_days])
            self.open_VIX_threshold = self.av_VIX * self.open_VIX
            self.close_VIX_threshold = self.av_VIX * self.close_vix



        #suma zmian zmienności (kolumna BJ)
        #wygładzanie
            self.differencePips.append(self.zmiana_w_pipsach_1_wersja2[-1] - self.zmiana_w_pipsach_2_wersja2[-1]) #BJ
            if len(self) ==3:
                self.ES= self.differencePips[0] 
            if len(self) == 4:
                self.ES_zmiany.append(self.differencePips[-1] * self.alpha + self.ES * (1 - self.alpha)) #pierwszy input w liście od BM11
            if len(self) >= 5:
                self.ES_zmiany.append(self.differencePips[-1] * self.alpha + self.ES_zmiany[-1]  * (1 - self.alpha))

            #if self.ticket is not None and len(self) == 329:

            today = len(self)
            if self.line.idx > self.warmup and today > self.pip_av_days and today > self.n_days and today>self.av_VIX_days:
                #średnia wartość pipsa z X dni
                self.Pair1PipsValueCurrent = 1/np.array(self.datas[0].get(size=self.pip_av_days)) * self.volume *0.0001 #X
                self.Pair2PipsValueCurrent = 1/np.array(self.datas[1].get(size=self.pip_av_days)) * self.volume *0.0001 #Y
                
                #self.VIX = self.datas[6].close[0]
                self.carry_sum_daily = self.Pair1_swap_long + self.Pair2_swap_short

                #średnia zmienność pipsa z ostatnich Y dni
                # 1 PARA 
                ceny1 = np.array(self.datas[0].get(size=self.n_days+1))
                zmiana_ceny1 = abs(ceny1[1:] - ceny1[:-1]) #dzienna zmiana ceny       
                zmiana_w_pipsach1 = np.abs(zmiana_ceny1 * 10000) # dzienna zmiana ceny w pipsach kolumna AK
                srednia_zmiana_w_pipsach1 = np.mean(zmiana_w_pipsach1)
                srednia_zmiana_w_pipsach1_30d = np.mean(self.Pair1PipsValueCurrent[-self.pip_av_days:]) #AF
                # 2 PARA
                ceny2 = np.array(self.datas[1].get(size=self.n_days+1))
                zmiana_ceny2 = abs(ceny2[1:] - ceny2[:-1]) #dzienna zmiana ceny 
                zmiana_w_pipsach2 = np.abs(zmiana_ceny2 * 10000) #dzienna zmiana ceny w pipsach  kolumna AL
                srednia_zmiana_w_pipsach2 = np.mean(zmiana_w_pipsach2)
                srednia_zmiana_w_pipsach2_30d = np.mean(self.Pair2PipsValueCurrent[-self.pip_av_days:]) #AG
                
                #zmiana dzienna ceny w pipsach do kolumny BJ
                self.dailyPipDifference = (np.abs(zmiana_ceny1[:-1] * 10000)) - (np.abs(zmiana_ceny2[:-1] * 10000))
                #moduł zmienności w pipsach z ostatnich max 480 dni (AN bez mnożenia przez AG) 
                ceny_module1 = np.array(self.datas[0].get(size=len(self)-1)) 
                zmiana_ceny_module_1 = abs(ceny_module1[1:] - ceny_module1[:-1])
                srednia_zmiana_ceny_module_1 = np.abs(zmiana_ceny_module_1 * 10000) #AK
                module1 = np.mean(srednia_zmiana_ceny_module_1)

                 #moduł zmienności w pipsach z ostatnich max 480 dni (AN bez mnożenia przez AG) 
                ceny_module2 = np.array(self.datas[1].get(size=len(self)-1))
                zmiana_ceny_module_2 = abs(ceny_module2[1:] - ceny_module2[:-1])
                srednia_zmiana_ceny_module_2 = np.abs(zmiana_ceny_module_2 * 10000) #AL
                module2 = np.mean(srednia_zmiana_ceny_module_2)

                am = module1 * srednia_zmiana_w_pipsach1_30d #AM
                an = module2 * srednia_zmiana_w_pipsach2_30d #AN
                
                self.size1 = module2 / (module1 + module2) * self.volume
                self.size2 = module1 /(module1 + module2) * self.volume
                
                ao = an/am #usddkk
                ap = 1 #usdpln

                self.vol1 = 100000 * ao #usddkk
                self.vol2 = -100000 * ap #usdpln 
                
                if len(self) <= self.max_module_period:
                #średnia wygładzania od początku
                    all_smooth_av = sum(self.ES_zmiany)/ (len(self)-3)
                    self.cena1_1 = self.datas[0].close[0]
                    self.cena2_2 = self.datas[1].close[0]
                    if self.ticket is None and self.ES_zmiany[-1] < (all_smooth_av * self.open_threshold) and self.carry_sum_daily > self.min_swap and self.VIX < self.open_VIX_threshold:
                        self.ticket = 1
                        self.vol1open = self.vol1 #wolumen otwarcia 1 pozycji
                        self.vol2open = self.vol2 #wolumen otwarcia 2 pozycji
                        self.openingPrice1 = self.datas[0].close[0]
                        self.openingPrice2 = self.datas[1].close[0]

                    if self.ticket is not None:
                        if self.ES_zmiany[-1] > (all_smooth_av * self.close_threshold) or self.VIX > self.close_VIX_threshold or self.carry_sum_daily < self.min_swap:
                            self.ticket = None
                            self.closeBuyValue = self.cena1_1 * self.vol1open
                            self.closeSellValue = self.cena2_2 * self.vol2open
                            self.openingPrice1 = None
                            self.openingPrice2 = None
                            self.vol1open = None
                            self.vol2open = None

                if len(self) > self.max_module_period:
                    all_smooth_av = sum(self.ES_zmiany[-self.max_module_period:]) / self.max_module_period
                    self.cena1_1 = self.datas[0].close[0]
                    self.cena2_2 = self.datas[1].close[0]
                    if self.ticket is None and self.ES_zmiany[-1] < (all_smooth_av * self.open_threshold) and self.carry_sum_daily > self.min_swap and self.VIX < self.open_VIX_threshold:
                        self.ticket = 1
                        self.buyValue = self.cena1_1 * self.vol1 #wartość otwarcia pozycji 1 
                        self.sellValue = self.cena2_2 * self.vol2 #wartość otwarcia pozycji 2 
                        self.vol1open = self.vol1 #wolumen otwarcia 1 pozycji
                        self.vol2open = self.vol2 #wolumen otwarcia 2 pozycji
                        self.value_USD = self.buyValue/self.cena1_1 + self.sellValue/self.cena2_2
                        self.openingPrice1 = self.datas[0].close[0]
                        self.openingPrice2 = self.datas[1].close[0]
                    
                    if self.ticket is not None:
                        if self.ES_zmiany[-1] > (all_smooth_av * self.close_threshold) or self.VIX > self.close_VIX_threshold or self.carry_sum_daily < self.min_swap:
                            self.ticket = None
                            self.closeBuyValue = self.cena1_1 * self.vol1open
                            self.closeSellValue = self.cena2_2 * self.vol2open
                            self.openingPrice1 = None
                            self.openingPrice2 = None
                            self.vol1open = None
                            self.vol2open = None

            if self.ticket is not None:
                self.carry1 = ((self.Pair1_swap_long * self.vol1 * self.datas[0].close[0])/self.datas[0].close[0])
                self.carry2 = ((self.Pair2_swap_short * self.vol2 * self.datas[1].close[0])/self.datas[1].close[0])
                cenka1 = self.datas[0].close[0]
                cenka2 = self.datas[1].close[0]
                self.holdingDateList.append(len(self))
                self.dailyP_L = ((self.vol1open * (cenka1 - self.openingPrice1))/cenka1) + ((self.vol2open * (cenka2 - self.openingPrice2))/cenka2)
                self.pair1_carry.append((self.datas[2].close[0] * self.vol1 * self.datas[0].close[0])/self.datas[0].close[0])
                self.pair2_carry.append((self.datas[3].close[0] * self.vol2 * self.datas[1].close[0])/self.datas[1].close[0])
                self.pair1_carry_sum = sum(self.pair1_carry)
                self.pair2_carry_sum = sum(self.pair2_carry)
                self.swapsSum = sum(self.pair1_carry + self.pair2_carry)


                #do sumy price changes ABS
                self.test_daily_change.append(abs(((self.vol1open * (self.datas[0].close[0] - self.datas[0].close[-1]))/self.datas[0].close[0]))
                + abs(((self.vol2open * (self.datas[1].close[0] - self.datas[1].close[-1]))/self.datas[1].close[0])))
                
                #do printowania price changes ABS
                self.testowy_daily_change = (((self.vol1open * (self.datas[0].close[0] - self.datas[0].close[-1]))/self.datas[0].close[0])
                + ((self.vol2open * (self.datas[1].close[0] - self.datas[1].close[-1]))/self.datas[1].close[0]))
                #do wyliczenia dziennych zmian cen
                self.test_daily_change_summary.append((((self.vol1open * (self.datas[0].close[0] - self.datas[0].close[-1]))/self.datas[0].close[0]))
                + (((self.vol2open * (self.datas[1].close[0] - self.datas[1].close[-1]))/self.datas[1].close[0])))

                #suma zmian cen do podsumowania
                self.test_daily_change_summary_report = sum(self.test_daily_change_summary)
                #suma zmian cen ABS do optymalizacji
                self.test_sum = sum(self.test_daily_change)
                #do ratio swapy/swapy
                self.test_swap_priceChange = self.swapsSum
                #self.swap_by_profit = self.swapsSum / self.test_daily_change_summary_report

            if self.ticket is None: 
                self.dailyP_L = 0
                self.pair1_carry_last = 0
                self.pair2_carry_last = 0
                self.pair1_carry.append(0)
                self.pair2_carry.append(0)
                self.test_daily_change_summary.append(0)
                self.testowy_daily_change = 0
                self.test_daily_change.append(0)
                self.swapsSum = sum(self.pair1_carry + self.pair2_carry)
                self.test_daily_change_summary_report = sum(self.test_daily_change_summary)
                self.vol1open = 0
                self.vol2open = 0