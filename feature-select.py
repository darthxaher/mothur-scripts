import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def load_dataset(shread_path, design_path, design_int_maps):
    # load dataset
    shared = pd.read_table('WTmiceonly_final.shared')
    design = pd.read_table('WTmiceonly_final.design', header=None)

    shared.drop(['Group', 'label', 'numOtus'], axis=1, inplace=True)
    for k in design_int_maps.keys():
        design.loc[design[1] == k, 1] = design_int_maps[k]
    # this is needed to change the datateype to numeric 
    # as the original data is string/object type in the column
    design[1] = pd.to_numeric(design[1])

    print('Number of input features: {}'.format(len(shared.keys())))
    return shared, design


def preprocess_data(shared, design, std_percent, corr_threshold):
    # dataset is ready for analysis
    # first remove almost null columns
    stddevs = shared.std()
    std_threshold = stddevs.max() * std_percent
    filtered = stddevs[stddevs > std_threshold]
    shared = shared[filtered.keys()]
    print('Number of input features after standard deviation based pruning: {}'.format(len(shared.keys())))

    pearson_corr = shared.corr()

    keys = pearson_corr.keys()
    dupes = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            x, y = keys[i], keys[j]
            if y in dupes: continue
            # print(x, y, pearsons[x][y])
            if pearson_corr[x][y] > corr_threshold or pearson_corr[x][y] < -corr_threshold:
                dupes.append(y)
    shared = shared.drop(dupes, axis=1)
    print('Number of input features after pearson\'s correlation check with threshold value {}: {}' \
          .format(corr_threshold, len(shared.keys())))
    return shared, design


def select_features_univariate(X, y, percentile):
    # univariate feature selection with chi square test
    from sklearn.feature_selection import SelectPercentile
    from sklearn.feature_selection import chi2

    X_new = pd.DataFrame(SelectPercentile(score_func=chi2, percentile=percentile).fit_transform(X, y))

    # calculate the hash value for each of the orignal columns
    hashes = {}
    features_selected = []
    for c in X.keys(): hashes[hash(tuple(X[c].values))] = c
    # use the old hash values to find the column names now
    for c in X_new.keys():
        features_selected.append(hashes[hash(tuple(X_new[c].values))])
    print('Here are the most important features from univariate chi square test: {}'.format(features_selected))


def select_features_svm_rfe(X, y, cross_val_folds):
    # recursive feature elimination with SVM
    # http://scikit-learn.org/stable/auto_examples/feature_selection/plot_rfe_with_cross_validation.html
    from sklearn.feature_selection import RFECV
    from sklearn.svm import SVC
    from sklearn.model_selection import StratifiedKFold
    from sklearn.model_selection import KFold

    svc = SVC(kernel='linear')
    cross_validator = StratifiedKFold(n_splits=cross_val_folds, shuffle=True)
    # cross_validator = KFold(n_splits=cross_val_folds)
    rfecv = RFECV(estimator=svc, step=1, cv=cross_validator, scoring='accuracy', verbose=0, n_jobs=-1)
    rfecv.fit(X, y)
    print("Optimal number of features : %d" % rfecv.n_features_)
    ranking_svm_rfe = pd.Series(rfecv.ranking_, index=X.keys())
    ranking_svm_rfe.sort_values(inplace=True)
    print('Feature ranking with SVM-RFE\n:{}'.format(ranking_svm_rfe))

    # Plot number of features VS. cross-validation scores
    plt.figure()
    plt.xlabel("Number of features selected")
    plt.ylabel("Cross validation score (nb of correct classifications)")
    plt.plot(range(1, len(rfecv.grid_scores_) + 1), rfecv.grid_scores_)
    plt.show()


def select_features_rforest(X, y, numforests):
    from sklearn.ensemble import RandomForestClassifier

    # more experiment with radom forests
    rfc = RandomForestClassifier(n_estimators=numforests, criterion='entropy', \
        oob_score=True, n_jobs=-1, verbose=1, class_weight='balanced')
    rfc.fit(X, y)
    ranking_rforest = pd.Series(rfc.feature_importances_, index=X.keys())
    ranking_rforest.sort_values(inplace=True, ascending=False)
    print('Feature ranking with random forest:\n{}'.format(ranking_rforest))


if __name__ == '__main__':
    # parameters
    std_percent = 0.01  # should be 0.01 normally
    corr_threshold = 0.8
    shared, design = load_dataset('WTmiceonly_final.shared', 'WTmiceonly_final.design', \
                                  {'Before': 0, 'After1': 1, 'After2': 2, 'After3': 3})
    shared, design = preprocess_data(shared, design, std_percent, corr_threshold)
    X, y = shared, design[1]

    select_features_univariate(X, y, percentile=10)
    select_features_svm_rfe(X, y, cross_val_folds=5)
    select_features_rforest(X, y, numforests=1000)
