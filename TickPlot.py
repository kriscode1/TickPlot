'''Reads print and quote data for a single stock in SpryWare format, 
colorizes the prints, and displays the data in an interactive matplotlib plot.

This version can either plot with evenly spaced time intervals (to emphasize 
price stability instead of change over time), or plot with the x axis 
representing time as expected.
To plot in uniform time intervals, set the PLOT_UNIFORM_TIME_INTERVALS bool 
to True.

To connect the prints or quotes points with lines, set the 
CONNECT_PRINTS_WITH_LINE and CONNECT_QUOTES_WITH_LINE bools to True.
'''

import matplotlib.pyplot as plt
#python -m pip install matplotlib
from matplotlib.widgets import Button
import math    #for transform_size_to_plot_area()
from decimal import *
import sys

TRADES_FILE_PATH = ""
QUOTES_FILE_PATH = ""
PLOT_UNIFORM_TIME_INTERVALS = True
CONNECT_PRINTS_WITH_LINE = False
CONNECT_QUOTES_WITH_LINE = False

if (TRADES_FILE_PATH == "") or (QUOTES_FILE_PATH == ""):
    print("Forgot to set path constants.")
    sys.exit()

########### Read data & prepare for plotting ###########

def price_to_decimal(raw_price, scale):
    '''Converts SpryWare prices to Decimal objects.'''
    ret = Decimal(raw_price)
    for x in range(scale):
        ret = ret/10
    return ret

def split_time_str(time_str):
    '''Converts SpryWare times to a 3-tuple of floats.
    
    Floats are desirable because SpryWare decimalizes seconds.
    '''
    nums = time_str.split(":")
    if (len(nums) != 3):
        print("Error TimeStrToInts time_str=" + str(time_str) + 
              ", nums=" + str(nums))
        return None
    else:
        return (float(nums[0]), float(nums[1]), float(nums[2]))

def time_tuple_to_seconds(time_tuple):
    '''Converts split_time_str() output to a single float.
    
    The returned float is the number of seconds since the day began, for easy 
    sorting by time.
    '''
    (hh, mm, ss) = time_tuple
    return ss+mm*60+hh*3600

def time_str_to_seconds(time_str):
    '''Converts SprWare times to a single float. 
    
    The returned float is the number of seconds since the day began, for easy 
    sorting by time.
    '''
    return time_tuple_to_seconds(split_time_str(time_str))

def transform_size_to_plot_area(size):
    '''Weighted mapping of size/volume to point area for plotting.'''
    area = 0
    if size == 0:
        pass
    elif size < 100:
        area = math.ceil(size/20)#Will range between 1-5
    else:
        area = math.log10(size) + 4
    return int(2*area)

def is_good_trade_condition(tradeCondition):
    '''Boolean test of whether the SprWare trade condition is acceptable.
    
    The conditionExclusionList was made from looking at a table of SprWare 
    condition codes and their meaning.
    '''
    conditionExclusionList = [2, 3, 4, 5, 13, 14, 16, 18, 30, 32, 34, 57, 58, 
                              59, 63, 71, 72, 102, 105, 145]
    for condition in conditionExclusionList:
        if tradeCondition == condition:
            return False
    return True

def get_trades_tuples(filename):
    '''Parses a SpryWare trades/prints file into a list of tuples containing 
    only the data of interest.
    
    At present, this returns a list of 3-tuples:
    (time, tradePrice, tradeSize)
    where:
    time is a float of the number of seconds since the day began,
    tradePrice is a Decimal object
    tradeSize is an int
    '''
    f = open(filename, 'r')
    trades_tuples = []
    for line in f:
        cells = line.split(',')
        if len(cells) != 11:
            print("Split into "+str(len(cells))+", done reading.")
            f.close()
            return trades_tuples
        else:
            #date = cells[0]    #Still a string
            time = split_time_str(cells[1])
            #symbol = cells[2]
            #transType = cells[3]
            #itemType = int(cells[4])
            condition = int(cells[5])
            scale = int(cells[6])
            #sequence = int(cells[7])
            #tradeExchange = cells[8]
            tradePrice = price_to_decimal(cells[9], scale)
            tradeSize = int(cells[10])
            if is_good_trade_condition(condition):
                trades_tuples.append((time, tradePrice, tradeSize))
    f.close()
    return trades_tuples

def get_quotes_tuples(filename):
    '''Parses a SpryWare quotes file into a list of tuples containing only 
    the data of interest.
    
    At present, this returns a list of 5-tuples:
    (time, bidPrice, bidSize, askPrice, askSize)
    where:
    time is a float of the number of seconds since the day began,
    bidPrice and askPrice are both Decimal objects
    bidSize and askSize are both ints
    '''
    f = open(filename, 'r')
    quotes_tuples = []
    for line in f:
        cells = line.split(',')
        if len(cells) != 14:
            print("Split into "+str(len(cells))+", done reading.")
            f.close()
            return quotes_tuples
        else:
            #date = cells[0]    #Still a string
            time = split_time_str(cells[1])
            #symbol = cells[2]
            #transType = cells[3]    #Test these for expected values?
            #itemType = int(cells[4])
            #condition = int(cells[5])
            scale = int(cells[6])
            #sequence = int(cells[7])
            #bidExchange = cells[8]
            bidPrice = price_to_decimal(cells[9], scale)
            bidSize = int(cells[10])
            #askExchange = cells[11]
            askPrice = price_to_decimal(cells[12], scale)
            askSize = int(cells[13])
            quotes_tuples.append((time, bidPrice, bidSize, askPrice, askSize))
    f.close()
    return quotes_tuples

trades_tuples = get_trades_tuples(TRADES_FILE_PATH)
quotes_tuples = get_quotes_tuples(QUOTES_FILE_PATH)

#Merge all events together into one sorted list
eventsSeq = []
print("Building events sequence.")
for (time, tradePrice, tradeSize) in trades_tuples:
    eventsSeq.append((time_tuple_to_seconds(time), 
                      "T", 
                      (tradePrice, tradeSize)))
for (time, bidPrice, bidSize, askPrice, askSize) in quotes_tuples:
    eventsSeq.append((time_tuple_to_seconds(time), 
                      "Q", 
                      (bidPrice, bidSize, askPrice, askSize)))
print("Sorting "+str(len(eventsSeq))+" events.")
eventsSeq = sorted(eventsSeq, key=lambda infoTuple: infoTuple[0])
print("Sorted.")

######### Prepare the trades and quotes for plotting together as events

lastBid = None
lastOffer = None
lastBidSize = None
lastOfferSize = None
time_start = time_str_to_seconds("9:30:00.000")
time_end = time_str_to_seconds("11:00:00.000")
tradesTimeSeq = []

#y_, s_, and x_ variables are for plotting in matplotlib
#(x_, y_) coordinates with size s_
y_trades = []
s_trades = []
x_trades = []
y_bids = []
s_bids = []
y_offers = []
s_offers = []
x_quotes = []    #Bids and offers share the same time index
#quotesTimeSeq = []

#Variables for assigning color per print
y_redPrints = []
s_redPrints = []
x_redPrints = []
y_greenPrints = []
s_greenPrints = []
x_greenPrints = []

print("Looping the events.")
#This entire loop is indexed by trades, and quotes are only recorded for each 
#trade. If PLOT_UNIFORM_TIME_INTERVALS is True, the plot will have even time 
#intervals between each trade print. If PLOT_UNIFORM_TIME_INTERVALS is False, 
#time will be plotted as expected, often with many trades squeezed into a 
#small interval.
xIndex = 0
for (time, code, infoTuple) in eventsSeq:
    if (time >= time_start) and (time <= time_end):
        if code == "Q":
            (lastBid, lastBidSize, lastOffer, lastOfferSize) = infoTuple
            #quotesTimeSeq.append(time)
        if code == "T" and (lastBid != None):
            #Add the last quote to plot
            y_bids.append(lastBid)
            s_bids.append(transform_size_to_plot_area(lastBidSize))
            y_offers.append(lastOffer)
            s_offers.append(transform_size_to_plot_area(lastOfferSize))
            if PLOT_UNIFORM_TIME_INTERVALS:
                x_quotes.append(xIndex)
            else:
                x_quotes.append(time)
            
            #Now handle the trade itself
            (tradePrice, tradeSize) = infoTuple
            y_trades.append(tradePrice)
            s_trades.append(transform_size_to_plot_area(tradeSize))
            if PLOT_UNIFORM_TIME_INTERVALS:
                x_trades.append(xIndex)
            else:
                x_trades.append(time)
            
            #Process print colors
            if (tradePrice == lastBid):
                #Red print
                y_redPrints.append(tradePrice)
                s_redPrints.append(transform_size_to_plot_area(tradeSize))
                if PLOT_UNIFORM_TIME_INTERVALS:
                    x_redPrints.append(xIndex)
                else:
                    x_redPrints.append(time)
            elif (tradePrice == lastOffer):
                #Green print
                y_greenPrints.append(tradePrice)
                s_greenPrints.append(transform_size_to_plot_area(tradeSize))
                if PLOT_UNIFORM_TIME_INTERVALS:
                    x_greenPrints.append(xIndex)
                else:
                    x_greenPrints.append(time)
            else:
                #White print
                pass
            xIndex += 1

########### Plot Data ###########

print("Begin plotting.");
fig, ax1 = plt.subplots()

if CONNECT_PRINTS_WITH_LINE:
    ax1.plot(x_trades, y_trades, 
             marker=None, linestyle='-', color='blue', alpha=0.5)
ax1.scatter(x_trades, y_trades, s=s_trades, color='blue', alpha=0.5)
if CONNECT_QUOTES_WITH_LINE:
    ax1.plot(x_quotes, y_bids, 
             marker=None, linestyle='-', color='c', alpha=0.5)
ax1.scatter(x_quotes, y_bids, s=s_bids, color='c', alpha=0.5)
if CONNECT_QUOTES_WITH_LINE:
    ax1.plot(x_quotes, y_offers, 
             marker=None, linestyle='-', color='m', alpha=0.5)
ax1.scatter(x_quotes, y_offers, s=s_offers, color='m', alpha=0.5)
ax1.scatter(x_redPrints, y_redPrints, s=s_redPrints, color='r', alpha=1.0)
ax1.scatter(x_greenPrints, y_greenPrints, s=s_greenPrints, 
            color='g', alpha=1.0)
ax1.grid(b=True, which='major', axis='y', alpha=0.6)
ax1.grid(b=True, which='minor', axis='y', alpha=0.3)
ax1.ticklabel_format(useOffset=False, style='plain')

########### Build interactive zooming features ###########

def zoom_factory(ax,base_scale = 2.0):
    '''Handles zooming when the mouse scrollwheel is used.
    
    Based someone else's code.
    Credit to: 
    http://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel
    '''
    def zoom_fun(event):
        # get the current x and y limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
        cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1/base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            print(event.button)
        # set new limits
        ax.set_xlim([xdata - cur_xrange*scale_factor,
                     xdata + cur_xrange*scale_factor])
        ax.set_ylim([ydata - cur_yrange*scale_factor,
                     ydata + cur_yrange*scale_factor])
        plt.draw() # force re-draw
    fig = ax.get_figure() # get the figure of interest
    # attach the call back
    fig.canvas.mpl_connect('scroll_event',zoom_fun)
    #return the function
    return zoom_fun

zoom_event_handler = zoom_factory(ax1, base_scale=1.1)

#Zooming time buttons, x axis
#Coordinates lists: [left, bottom, width, height]
button_ZoomInTime_ax = plt.axes([0.8, 0.025, 0.15, 0.04])
button_ZoomInTime = Button(button_ZoomInTime_ax, 'Zoom In Time', 
                           color='lightblue', hovercolor='white')
button_ZoomOutTime_ax = plt.axes([0.6, 0.025, 0.18, 0.04])
button_ZoomOutTime = Button(button_ZoomOutTime_ax, 'Zoom Out Time', 
                            color='lightblue', hovercolor='white')

def button_ZoomTime_handler(scale_factor):
    '''Handles zooming of time when the appropriate buttons are pressed.'''
    def button_ZoomTime_handler_withScale(event):
        cur_xlim = ax1.get_xlim()
        xrange = cur_xlim[1] - cur_xlim[0]
        if scale_factor < 1.0:
            ax1.set_xlim([(cur_xlim[0]+xrange*scale_factor), 
                          (cur_xlim[1]-xrange*scale_factor)])
        else:
            ax1.set_xlim([(cur_xlim[0]-xrange*scale_factor), 
                          (cur_xlim[1]+xrange*scale_factor)])
        plt.draw()
    return button_ZoomTime_handler_withScale

button_ZoomInTime.on_clicked(button_ZoomTime_handler(0.3))
button_ZoomOutTime.on_clicked(button_ZoomTime_handler(1.3))

#Zooming price buttons, y axis
#Coordinates lists: [left, bottom, width, height]
button_ZoomInPrice_ax = plt.axes([0.3, 0.025, 0.15, 0.04])
button_ZoomInPrice = Button(button_ZoomInPrice_ax, 'Zoom In Price', 
                            color='lightblue', hovercolor='white')
button_ZoomOutPrice_ax = plt.axes([0.1, 0.025, 0.2, 0.04])
button_ZoomOutPrice = Button(button_ZoomOutPrice_ax, 'Zoom Out Price', 
                             color='lightblue', hovercolor='white')

def button_ZoomPrice_handler(scale_factor):
    '''Handles zooming of price when the appropriate buttons are pressed.'''
    def button_ZoomPrice_handler_withScale(event):
        cur_ylim = ax1.get_ylim()
        yrange = cur_ylim[1] - cur_ylim[0]
        if scale_factor < 1.0:
            ax1.set_ylim([(cur_ylim[0]+yrange*scale_factor), 
                          (cur_ylim[1]-yrange*scale_factor)])
        else:
            ax1.set_ylim([(cur_ylim[0]-yrange*scale_factor), 
                          (cur_ylim[1]+yrange*scale_factor)])
        plt.draw()
    return button_ZoomPrice_handler_withScale

button_ZoomInPrice.on_clicked(button_ZoomPrice_handler(0.3))
button_ZoomOutPrice.on_clicked(button_ZoomPrice_handler(1.3))

plt.show()
