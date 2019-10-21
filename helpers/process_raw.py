from bs4 import BeautifulSoup
import os


def process_raw(file):
    with open(file) as f:
        res = BeautifulSoup(f.read(), 'html.parser')
    games = res.find('ul', {'class': 'game-list-results-container'})
    names = [x['data-game-title'] for x in games.find_all('a')]
    return names


if __name__ == "__main__":
    all_names = []
    for rf in os.listdir('raw_data'):
        all_names.extend(process_raw('raw_data/'+rf))

    with open('real_games.txt', 'w') as o:
        o.writelines('\n'.join(all_names))
