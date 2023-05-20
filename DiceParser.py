import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as st
import re
import random


class die:
    def __init__(self, sides):
        self.sides = sides
        self.roll_val = 0
        self.cascade_val = 0
        self.roll_list = []
        self.cascade_list = []

    def roll(self, m):
        self.roll_list = [random.randint(1, self.sides) for i in range(abs(m))]
        if m < 0:
            self.roll_list = [-i for i in self.roll_list]
        self.roll_val = sum(self.roll_list)

    def cascade(self, m, c):
        self.roll(m)
        self.cascade_list.append(self.roll_list)
        self.cascade_val += self.roll_val
        while self.sides in self.roll_list:
            crit = self.roll_list.count(self.sides)
            self.roll(crit*c)
            self.cascade_list.append(self.roll_list)
            self.cascade_val += self.roll_val


def ProcessRoll(roll):
    validChar = "1234567890+-dc"
    validDie = ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]

    check = [i for i in roll if i not in validChar]
    flag = not check

    if not flag:
        unique = ''.join(list(dict.fromkeys(check)))
        print("The following characters are not valid: "+unique)
        print("Please try again.")
        return flag, 0, []

    temp = roll
    for i in validDie:
        temp = re.sub(i, "", temp)
    flag = 'd' not in temp

    if not flag:
        temp = temp.replace("+", ";+").replace("-", ";-").split(';')
        temp = ["d" + i.split('d')[1] for i in temp if 'd' in i]
        print("The following non-standard dice are not supported: ")
        for i in temp:
            print(i)
        print("Please try again.")
        return flag, 0, []

    roll = roll.replace("+", ";+").replace("-", ";-").split(';')
    check = [i for i in roll if i=='']
    if check:
        roll.remove('')

    dice = [i.split('d') for i in roll if 'd' in i]
    mods = [i for i in roll if 'd' not in i]

    for i in dice:
        flag = i[0].isdigit() or i[0][1:].isdigit()
        if not flag:
            i[0] += '1'

    temp = [i for i in roll if 'd' in i]
    check = list(set(roll) - set(temp))
    flag = mods == check

    if not flag:
        print("Your original roll contains unused operators.")
        print("Please confirm this is the correct form of your roll: ")
        temp = mods + temp
        temp = ''.join(temp).replace("+", " + ").replace("-", " - ")
        print(temp)
        yn = ''
        while yn != 'y' and yn != 'n':
            yn = str(input("[y]/[n]? "))

        if yn == 'n':
            print("Please try again.")
            return flag, 0, []

    mod_val = sum(map(int, mods))

    return flag, mod_val, dice


def Roller(mod_val, dice):

    total = mod_val
    multi = [int(i[0]) for i in dice]
    explode = [list(map(int, i[1].split('c'))) for i in dice]
    ind = [i for i, x in enumerate(list(map(len, explode))) if x == 1]
    for i in ind:
        explode[i].append(0)


    for i in range(len(multi)):
        d = die(explode[i][0])
        m = multi[i]
        c = explode[i][1]

        d.cascade(m, c)
        total += d.cascade_val
    return total


def RollStats(mod_val, dice, show_total=0, prod=1, power=6):

    multi = [int(i[0]) for i in dice]
    explode = [list(map(int, i[1].split('c'))) for i in dice]
    ind = [i for i, x in enumerate(list(map(len, explode))) if x == 1]
    for i in ind:
        explode[i].append(0)

    columns = []
    rows = []
    if mod_val:
        columns.append("modifier")
        rows.append(mod_val)
    for i in range(len(multi)):
        columns.append(str(multi[i])+"d"+dice[i][1])
    columns.append("total")

    df = pd.DataFrame(columns=columns)

    x0 = 2**32
    x1 = 0
    sample = prod*10**power
    res = prod*10**(power-4)
    for k in range(sample):
        total = mod_val
        row = rows[:]
        for i in range(len(multi)):
            d = die(explode[i][0])
            m = multi[i]
            c = explode[i][1]
            d.cascade(m, c)
            val = d.cascade_val
            row.append(val)
            total += val

        x0 = min(x0, total)
        x1 = max(x1, total)

        if k % res == 0:
            row.append(total)
            df.loc[k/res] = list(map(float, row))

    if not show_total:
        df = df.drop("total", axis=1)
        columns.remove("total")

    print(df.describe())

    plt.rcParams.update({'font.size': 10, 'axes.linewidth': 1, 'font.family': 'Arial'})
    for i in columns:
        if not i == "modifier":
            df_mean = np.mean(df[i])
            df_std = np.std(df[i])

            pdf = st.norm.pdf(df[i].sort_values(), df_mean, df_std)

            fig, ax = plt.subplots(1, 1, figsize=(1, 1), dpi=300)

            mean_label = "Mean: "+str(round(df_mean, 2))
            plus_minus = u"\u00B1"
            std_label = "SD: "+plus_minus+str(round(df_std, 2))
            min_roll_label = "Minimum of " + str(prod) + u"\u00D7" + f'10$^{{{power}}}$' + " rolls: " + str(x0)
            max_roll_label = "Maximum of "+str(prod)+u"\u00D7"+f'10$^{{{power}}}$'+" rolls: "+str(x1)
            plot_label = i
            if i == "total":
                plot_label = ' + '.join(columns[:-1])

            ax.plot(df[i].sort_values(), pdf, linewidth=1.5, label="Probability Density")
            ax.plot([df_mean, df_mean], [min(pdf), max(pdf)], linewidth=1, linestyle='--', label=mean_label)
            ax.plot([df_mean+df_std, df_mean+df_std, df_mean-df_std, df_mean-df_std],
                    [0.68*max(pdf), 0, 0, 0.68*max(pdf)],
                    linewidth=1, linestyle='--', label=std_label)
            ax.plot(x0, pdf[0], marker='o', ms=1, mfc='w', linestyle='none', label=min_roll_label)
            ax.plot(x1, pdf[-1], marker='o', ms=1, mfc='w', linestyle='none', label=max_roll_label)
            ax.set_title(plot_label)
            ax.set_xlabel("Roll Total", size=10)
            ax.set_ylabel("Frequency", size=10)
            tick = list(range(x0, x1, round(x1/10)))
            if x1 not in tick:
                tick.append(x1)
            ax.set_xticks(tick)
            ax.set_yticks([q*0.01 for q in range(1, 31, 2)])
            ax.set_xlim([x0, x1])
            ax.set_ylim([min(pdf), max(pdf) + 0.005])
            ax.legend(loc='upper right', fontsize=5, handletextpad=0.1, borderpad=0.3, framealpha=1, edgecolor='black')
            plt.gcf().subplots_adjust(bottom=0.22, left=0.15)

    plt.show()


def RollAgain():
    again = ''
    while again != 'y' and again != 'n':
        again = str(input("Keep rolling? [y]/[n]: "))
    if again == 'y':
        main()


def main():
    flag = 0
    stats = 0
    # stat_check = ''
    # while stat_check != 'y' and stat_check != 'n':
    #     stat_check = str(input("Run stats [y]/[n]? "))
    #
    # stats = stat_check == 'y'
    while not flag:
        roll_script = "d20"
        if not stats:
            roll_script = str(input("Enter dice to be rolled and modifiers: "))
        roll_script = re.sub(" ", "", roll_script)
        flag, mod_val, dice = ProcessRoll(roll_script)

    if not stats:
        advantage = ''
        if len(dice) == 1 and dice[0][1] == '20':
            while advantage != 'y' and advantage != 'n':
                advantage = str(input("With advantage? [y]/[n]: "))
        adv = advantage == 'y'

        if not adv:
            total = Roller(mod_val, dice)
            print("Roll total:", total, "\n")

            RollAgain()

            return

        total1 = Roller(mod_val, dice)
        total2 = Roller(mod_val, dice)
        print("First roll:", total1)
        print("Second roll:", total2)

        RollAgain()

        return

    RollStats(mod_val, dice)

    # show_total = 0
    # prod = 1
    # power = 6
    # RollStats(mod_val, dice, show_total, prod, power)

if __name__ == "__main__":
    main()