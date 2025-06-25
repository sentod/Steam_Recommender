import loadData
import view

import entities

hardwareDataset = entities.hardwareDataset()
gameDataset = entities.gameDataset()
userSteam = entities.userSteam()

loadData.load_dataframe(hardwareDataset, gameDataset)
if view.search_input(userSteam) :
    loadData.extract_genres_categories(gameDataset)
    view.user_summaries_widget(userSteam, gameDataset)
    view.user_spec_input(hardwareDataset, userSteam)
    view.recommendation_result(gameDataset, userSteam, hardwareDataset)