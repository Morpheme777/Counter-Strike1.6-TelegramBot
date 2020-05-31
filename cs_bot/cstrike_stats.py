# pip install tabulate
# pip install pandas --upgrade

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import six
import json


from logs_parser import LogsParser


DAYS_DOUBLE_DECAY = 7
MIN_WEIGHTED_KILLS = 50
SMOOTH_WINDOW_DAYS = 5
WORK_DIR = os.path.dirname(os.path.realpath(__file__))
IMG_FOLDER = WORK_DIR + '/img'
DATA_FOLDER = WORK_DIR + '/data'

data_files = []
for file in os.listdir(DATA_FOLDER):
    if file.endswith(".json"):
        data_files.append(file)
data_files.sort()
dfs = []
for file in data_files:
    f = open("{}/{}".format(DATA_FOLDER,file), 'r')
    data = json.load(f)
    f.close()
    df = pd.DataFrame.from_records(data)
    dfs.append(df)

#df0 = pd.DataFrame.from_records(data)
#df1 = pd.DataFrame.from_records(data_1)
#dfs = [df0, df1]


def render_mpl_table_ranking(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    data['True Skill'] = data['True Skill'].apply(lambda x: "{:,.2f}".format(x))
    data['Trend'] = data['Trend'].apply(lambda x: "{:,.2f}".format(x))
    data['Player'] = data['Player'].apply(lambda x: x[:14])
    data.drop(labels='steam_id', inplace=True, axis=1)
    data.insert(0, 'Rank', np.arange(1, len(data)+1))

    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)
    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])

        if k[1] == 3 and k[0] > 0:
            if cell.get_text().get_text()[0] == '-':
                cell.get_text().set_color('red')
            else:
                cell.get_text().set_color('green')

    plt.tight_layout()
    plt.savefig(WORK_DIR + '/ranking.png')
    return ax


def main(dfs):
    users = dfs[-1].name.unique()
    steam_ids = dfs[-1].auth.unique()
    avg_damage = dfs[-1].damage.mean()
    avg_kills = dfs[-1].kills.mean()
    
    def _calc_skill(df_user, avg_damage, avg_kills):
        w = np.power(2, -np.arange(len(df_user))/DAYS_DOUBLE_DECAY)[::-1]
        kills_w = np.sum(df_user['kills'] * w)
        deaths_w = np.sum(df_user['deaths'] * w)
        damage_w = np.sum(df_user['damage'] * w)
        return kills_w / deaths_w * 0.5 * (avg_damage / avg_kills + damage_w / kills_w) , kills_w
    
    def _prepare_figure(user, accuracy, efficiency):
        ix = pd.isnull(accuracy) | pd.isnull(efficiency)
        accuracy = np.array(accuracy[~ix])
        efficiency = np.array(efficiency[~ix])
        x = range(len(accuracy))

        fig, ax1 = plt.subplots()
        plt.grid()
        plt.title(user)
        color = 'tab:blue'
        ax1.set_xlabel('day')
        ax1.set_ylabel('efficiency', color=color)
        ax1.plot(x, efficiency, color=color, alpha=0.5, linestyle=':')
        ax1.plot(x, pd.Series(efficiency).rolling(window=SMOOTH_WINDOW_DAYS, center=True).mean(), color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        color = 'tab:red'
        ax2.set_ylabel('accuracy', color=color)  # we already handled the x-label with ax1
        ax2.plot(x, accuracy, color=color, alpha=0.5, linestyle=':')
        ax2.plot(x, pd.Series(accuracy).rolling(window=SMOOTH_WINDOW_DAYS, center=True).mean(), color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()
        plt.savefig(f'{IMG_FOLDER}/{user}.png')
        plt.close(fig)
    
    
    for df in dfs:
        df['hits_total'] = df['hits'].apply(sum)
    
    cols = ['deaths', 'kills', 'damage', 'shots', 'hits_total']
    
    def prepare_user_info(dfs, user, steam_id):
        data = []
        for i, df in enumerate(dfs):
            try:
                if i == 0:
                    diffs = df[df.auth == steam_id][cols].iloc[0]
                else:
                    diffs = df[df.auth == steam_id][cols].iloc[0] - dfs[i-1][dfs[i-1].auth == steam_id][cols].iloc[0]
                data.append(diffs)
            except:
                pass
        if len(data) < 2:
            raise KeyError(f"no sufficient data for user {user}")
    
        user_dynamic_df = pd.DataFrame(data)
        user_dynamic_df['accuracy'] = user_dynamic_df['hits_total'] / user_dynamic_df['shots']
        user_dynamic_df['efficiency'] = user_dynamic_df['kills'] / (user_dynamic_df['deaths'] + user_dynamic_df['kills'])
        skill, kills_wheighted_count = _calc_skill(user_dynamic_df, avg_damage, avg_kills)
        skill_prev, _ = _calc_skill(user_dynamic_df[:-1], avg_damage, avg_kills)
        skill_diff = skill - skill_prev
        if kills_wheighted_count < MIN_WEIGHTED_KILLS:
            raise ValueError(f"not enough weighted kills for user {user}: {kills_wheighted_count}")
        _prepare_figure(user, user_dynamic_df['accuracy'], user_dynamic_df['efficiency'])
    
        return skill, skill_diff

    
    if not os.path.exists(IMG_FOLDER):
        os.mkdir(IMG_FOLDER)
    
    steam_id2nick = {}
    skill_data = []
    for steam_id in steam_ids:
        user = dfs[-1][(dfs[-1].auth==steam_id)]['name'].values[0]
        steam_id2nick[steam_id] = user
        #if steam_id == 'STEAM_0:0:1091943949':
        #    continue
        try:
            skill, skill_prev = prepare_user_info(dfs, user, steam_id)
        except Exception as e:
            print(steam_id, e)
            continue
        skill_data.append([steam_id, user, skill, skill_prev])
    
    df_ranking = pd.DataFrame(skill_data, columns=['steam_id', 'Player', 'True Skill', 'Trend']).sort_values('True Skill', ascending=False)
    df_ranking.reset_index(drop=True, inplace=True)
    return df_ranking, steam_id2nick

def render_pvp_matrix(players, pvp_matrix):
    fig, ax = plt.subplots()
    plt.title('Efficiency PvP')
    sns.heatmap(pvp_matrix, xticklabels=players, yticklabels=players, cmap='RdYlGn', ax=ax)
    plt.tight_layout()
    plt.savefig(WORK_DIR + '/pvp.png')

if __name__ == '__main__':
    df_ranking, steam_id2nick = main(dfs)

    lp = LogsParser('logs')
    stat_collector = lp.parse()

    steam_ids, pvp_matrix = stat_collector.get_pvp_stats()
    players = [steam_id2nick.get(s) for s in steam_ids]
    render_pvp_matrix(players, pvp_matrix)

    p2r = stat_collector.get_ratings()
    #df_ranking['new_rating'] = df_ranking.steam_id.apply(lambda x: p2r.get(x))
    render_mpl_table_ranking(df_ranking)