# =============================================================================
# Analyse Multivariée — League of Legends Match History (80k matches)
# Méthodes statistiques et étude de données
# =============================================================================

# 0. PACKAGES ------------------------------------------------------------------
packages <- c("tidyverse", "FactoMineR", "factoextra", "cluster",
              "corrplot", "knitr", "gridExtra", "scales",
              "caret", "randomForest")

installed <- packages %in% rownames(installed.packages())
if (any(!installed)) install.packages(packages[!installed])
lapply(packages, library, character.only = TRUE)

dir.create("figures", showWarnings = FALSE)
dir.create("output", showWarnings = FALSE)

# 1. CHARGEMENT ET JOINTURES ---------------------------------------------------

cat("Chargement des données...\n")

match_stats  <- read_csv("data/MatchStatsTbl.csv")
summoner_match <- read_csv("data/SummonerMatchTbl.csv")
match_tbl    <- read_csv("data/MatchTbl.csv")
rank_tbl     <- read_csv("data/RankTbl.csv")
champion_tbl <- read_csv("data/ChampionTbl.csv")

cat("MatchStatsTbl   :", nrow(match_stats),   "lignes\n")
cat("SummonerMatchTbl:", nrow(summoner_match), "lignes\n")
cat("MatchTbl        :", nrow(match_tbl),      "lignes\n")

# Jointures pour enrichir les stats avec champion, rang, lane
df_full <- match_stats %>%
  left_join(summoner_match, by = c("SummonerMatchFk" = "SummonerMatchId")) %>%
  left_join(match_tbl,      by = c("MatchFk" = "MatchId")) %>%
  left_join(rank_tbl,       by = c("RankFk"  = "RankId")) %>%
  left_join(champion_tbl,   by = c("ChampionFk" = "ChampionId"))

cat("Dataset joint   :", nrow(df_full), "lignes x", ncol(df_full), "colonnes\n")

# 2. ÉCHANTILLONNAGE -----------------------------------------------------------
# 732k lignes = trop lourd pour R ; on échantillonne 15 000 observations
# stratifié par Lane pour garder la représentativité des rôles

set.seed(42)

df_sample <- df_full %>%
  filter(!is.na(Lane), !Lane %in% c("NONE", "")) %>%
  group_by(Lane) %>%
  slice_sample(n = 3000) %>%   # 3000 par rôle = 15 000 total
  ungroup()

cat("Échantillon     :", nrow(df_sample), "lignes\n")
table(df_sample$Lane)

# 3. VARIABLES D'ANALYSE -------------------------------------------------------

vars_num <- c("kills", "deaths", "assists",
              "DmgDealt", "DmgTaken", "TurretDmgDealt",
              "TotalGold", "MinionsKilled", "visionScore",
              "DragonKills")

df_analyse <- df_sample %>%
  select(Lane, RankName, ChampionName, Win, all_of(vars_num)) %>%
  filter(complete.cases(.))

cat("Après sélection :", nrow(df_analyse), "lignes x", ncol(df_analyse), "colonnes\n")

# 4. PRÉPARATION DES DONNÉES ---------------------------------------------------

## 4.1 Valeurs manquantes
na_pct <- df_analyse %>%
  summarise(across(everything(), ~ round(mean(is.na(.)) * 100, 2))) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "pct_NA") %>%
  filter(pct_NA > 0)

if (nrow(na_pct) == 0) {
  cat("Aucune valeur manquante dans les variables sélectionnées.\n")
} else {
  print(na_pct)
}

## 4.2 Outliers — visualisation
df_analyse %>%
  select(all_of(vars_num)) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "valeur") %>%
  ggplot(aes(x = variable, y = valeur)) +
  geom_boxplot(fill = "#3498db", alpha = 0.6, outlier.color = "#e74c3c", outlier.size = 0.5) +
  facet_wrap(~variable, scales = "free") +
  labs(title = "Distribution et outliers par variable", x = "", y = "") +
  theme_minimal() +
  theme(axis.text.x = element_blank())

ggsave("figures/01_outliers_boxplots.png", width = 13, height = 8)

## 4.3 Suppression outliers (seuil 3 sigma) — boucle explicite sur colonnes num.
df_clean <- df_analyse

for (v in vars_num) {
  x <- as.numeric(df_clean[[v]])
  z <- as.numeric(abs(scale(x)))
  df_clean[[v]][z > 3] <- NA
}

df_clean <- df_clean[complete.cases(df_clean[, vars_num]), ]

cat("Après suppression outliers :", nrow(df_clean), "observations\n")

## 4.4 Statistiques descriptives par Lane
cat("Lanes présentes dans les données :", paste(unique(df_clean$Lane), collapse = ", "), "\n")

desc_lane <- df_clean %>%
  group_by(Lane) %>%
  summarise(across(all_of(vars_num), ~ round(mean(.x, na.rm = TRUE), 1),
                   .names = "moy_{.col}"),
            n = n()) %>%
  arrange(Lane)

print(desc_lane)
write_csv(desc_lane, "output/stats_descriptives_lane.csv")

## 4.5 Matrice de corrélation
mat_cor <- cor(df_clean %>% select(all_of(vars_num)))

png("figures/02_correlation_matrix.png", width = 900, height = 800)
corrplot(mat_cor,
         method = "color", type = "upper",
         addCoef.col = "black", number.cex = 0.7,
         tl.cex = 0.85,
         title = "Corrélations — Variables de performance LoL",
         mar = c(0,0,2,0))
dev.off()

# 5. ACP -----------------------------------------------------------------------

cat("\n--- ACP ---\n")

acp <- PCA(
  df_clean %>% select(all_of(vars_num)),
  scale.unit = TRUE,
  graph      = FALSE,
  ncp        = 5
)

## 5.1 Valeurs propres
eig <- get_eigenvalue(acp)
print(round(eig, 3))
write_csv(as.data.frame(eig), "output/acp_valeurs_propres.csv")

## 5.2 Scree plot
p_scree <- fviz_eig(acp,
                    addlabels = TRUE,
                    barfill   = "#2ecc71",
                    barcolor  = "#27ae60",
                    linecolor = "#e74c3c") +
  labs(title = "Éboulis des valeurs propres (Scree Plot)",
       x = "Composantes principales", y = "% variance expliquée") +
  theme_minimal()

print(p_scree)
ggsave("figures/03_acp_screeplot.png", p_scree, width = 8, height = 5)

## 5.3 Cercle des corrélations
p_var12 <- fviz_pca_var(acp, axes = c(1, 2),
                         col.var = "cos2",
                         gradient.cols = c("#3498db", "#e67e22", "#e74c3c"),
                         repel = TRUE,
                         title = "Cercle des corrélations — PC1 vs PC2") +
  theme_minimal()

p_var13 <- fviz_pca_var(acp, axes = c(1, 3),
                         col.var = "cos2",
                         gradient.cols = c("#3498db", "#e67e22", "#e74c3c"),
                         repel = TRUE,
                         title = "Cercle des corrélations — PC1 vs PC3") +
  theme_minimal()

ggsave("figures/04_acp_cercle_PC1_PC2.png", p_var12, width = 8, height = 7)
ggsave("figures/05_acp_cercle_PC1_PC3.png", p_var13, width = 8, height = 7)

## 5.4 Contributions
p_c1 <- fviz_contrib(acp, choice = "var", axes = 1, fill = "#3498db") +
  labs(title = "Contributions — PC1") + theme_minimal()
p_c2 <- fviz_contrib(acp, choice = "var", axes = 2, fill = "#e74c3c") +
  labs(title = "Contributions — PC2") + theme_minimal()

ggsave("figures/06_contributions_PC1.png", p_c1, width = 7, height = 5)
ggsave("figures/07_contributions_PC2.png", p_c2, width = 7, height = 5)

## 5.5 Projection individus colorés par Lane
lane_colors <- c("TOP"     = "#e74c3c",
                 "JUNGLE"  = "#2ecc71",
                 "MIDDLE"  = "#3498db",
                 "BOTTOM"  = "#f39c12",
                 "UTILITY" = "#9b59b6",
                 "SUPPORT" = "#e91e8c")

p_ind_lane <- fviz_pca_ind(acp,
                             axes        = c(1, 2),
                             geom        = "point",
                             habillage   = df_clean$Lane,
                             addEllipses = TRUE,
                             ellipse.type = "confidence",
                             palette     = lane_colors,
                             alpha.ind   = 0.3,
                             label       = "none",
                             title       = "Joueurs colorés par Lane — PC1 vs PC2") +
  theme_minimal()

ggsave("figures/08_acp_individus_lane.png", p_ind_lane, width = 10, height = 7)

# Coordonnées ACP pour clustering
n_axes <- sum(eig[, "eigenvalue"] > 1)
cat("Axes retenus (Kaiser) :", n_axes, "\n")
coords_acp <- acp$ind$coord[, 1:n_axes]

# 6. CLUSTERING ----------------------------------------------------------------

## 6.1 Nombre optimal de clusters
p_wss <- fviz_nbclust(coords_acp, kmeans, method = "wss",
                       k.max = 8, nstart = 25) +
  labs(title = "Méthode du coude") + theme_minimal()

p_sil <- fviz_nbclust(coords_acp, kmeans, method = "silhouette",
                       k.max = 8, nstart = 25) +
  labs(title = "Score de silhouette") + theme_minimal()

ggsave("figures/09_kmeans_k_optimal.png",
       arrangeGrob(p_wss, p_sil, ncol = 2), width = 13, height = 5)

## 6.2 K-means (k=5 : un cluster par rôle attendu)
k_optimal <- 5

set.seed(42)
km <- kmeans(coords_acp, centers = k_optimal, nstart = 50, iter.max = 200)
df_clean$cluster_km <- as.factor(km$cluster)

cat("\nTaille des clusters K-means :\n")
print(table(df_clean$cluster_km))

# Identifier automatiquement chaque cluster par ses stats dominantes
profils_tmp <- df_clean %>%
  group_by(cluster_km) %>%
  summarise(kills       = mean(kills),
            assists     = mean(assists),
            DmgDealt    = mean(DmgDealt),
            DmgTaken    = mean(DmgTaken),
            DragonKills = mean(DragonKills),
            visionScore = mean(visionScore),
            .groups = "drop")

# Règles d'affectation basées sur les stats les plus discriminantes
cluster_labels <- profils_tmp %>%
  mutate(label = case_when(
    assists     == max(assists)     ~ "Support/Utility",
    kills       == max(kills)       ~ "Carry dominant",
    DragonKills == max(DragonKills) ~ "Jungler",
    DmgDealt    == min(DmgDealt)    ~ "Support passif",
    TRUE                            ~ "Solo Laner (TOP/MID)"
  )) %>%
  select(cluster_km, label)

df_clean <- df_clean %>%
  left_join(cluster_labels, by = "cluster_km") %>%
  mutate(cluster_label = paste0("C", cluster_km, " – ", label))

cat("\nLabels des clusters :\n")
print(cluster_labels)

p_km <- fviz_cluster(km,
                      data         = coords_acp,
                      palette      = c("#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6"),
                      ellipse.type = "convex",
                      geom         = "point",
                      alpha        = 0.4,
                      ggtheme      = theme_minimal(),
                      main         = "Clusters K-means sur axes ACP")

ggsave("figures/10_kmeans_clusters.png", p_km, width = 10, height = 7)

## 6.3 CAH (sur sous-échantillon pour la lisibilité)
set.seed(42)
idx_cah  <- sample(nrow(coords_acp), 2000)
dist_mat <- dist(coords_acp[idx_cah, ], method = "euclidean")
cah      <- hclust(dist_mat, method = "ward.D2")

p_dend <- fviz_dend(cah,
                     k           = k_optimal,
                     cex         = 0.3,
                     palette     = c("#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6"),
                     rect        = TRUE,
                     rect_fill   = TRUE,
                     main        = "Dendrogramme CAH — Ward D2 (n=2000)") +
  theme_minimal()

ggsave("figures/11_cah_dendrogramme.png", p_dend, width = 12, height = 6)

df_clean$cluster_cah <- NA_character_
df_clean$cluster_cah[idx_cah] <- as.character(cutree(cah, k = k_optimal))

cat("\nComparaison K-means vs CAH (sous-échantillon) :\n")
print(table(KMeans = df_clean$cluster_km[idx_cah],
            CAH    = df_clean$cluster_cah[idx_cah]))

# 7. PROFILS DES CLUSTERS ------------------------------------------------------

profils <- df_clean %>%
  group_by(cluster_label) %>%
  summarise(across(all_of(vars_num), ~ round(mean(.x, na.rm = TRUE), 2)),
            Win_rate = round(mean(Win) * 100, 1),
            n        = n()) %>%
  arrange(cluster_label)

print(profils)
write_csv(profils, "output/profils_clusters.csv")

## Heatmap des profils
profils_long <- profils %>%
  select(-n, -Win_rate) %>%
  mutate(across(-cluster_label, ~ as.numeric(scale(.x)))) %>%
  pivot_longer(-cluster_label, names_to = "variable", values_to = "z_score")

p_heat <- ggplot(profils_long, aes(x = variable, y = cluster_label, fill = z_score)) +
  geom_tile(color = "white", linewidth = 0.5) +
  scale_fill_gradient2(low = "#3498db", mid = "white", high = "#e74c3c", midpoint = 0) +
  labs(title = "Heatmap des profils de clusters (z-scores)",
       x = "", y = "", fill = "Z-score") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

ggsave("figures/12_clusters_heatmap.png", p_heat, width = 11, height = 5)

## Composition des clusters par Lane
tab_lane <- df_clean %>%
  count(cluster_label, Lane) %>%
  group_by(cluster_label) %>%
  mutate(pct = round(n / sum(n) * 100, 1))

p_lane <- ggplot(tab_lane, aes(x = cluster_label, y = pct, fill = Lane)) +
  geom_col() +
  scale_fill_manual(values = lane_colors) +
  labs(title = "Composition des clusters par Lane",
       x = "", y = "%", fill = "Lane") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 20, hjust = 1))

ggsave("figures/13_clusters_composition_lane.png", p_lane, width = 11, height = 6)

## Composition par Rang
if ("RankName" %in% colnames(df_clean)) {
  tab_rank <- df_clean %>%
    count(cluster_label, RankName) %>%
    group_by(cluster_label) %>%
    mutate(pct = round(n / sum(n) * 100, 1))

  p_rank <- ggplot(tab_rank, aes(x = cluster_label, y = pct, fill = RankName)) +
    geom_col() +
    labs(title = "Composition des clusters par Rang",
         x = "", y = "%", fill = "Rang") +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 20, hjust = 1))

  ggsave("figures/14_clusters_composition_rang.png", p_rank, width = 11, height = 6)
}

# 8. BIPLOT FINAL --------------------------------------------------------------

p_biplot <- fviz_pca_biplot(acp,
                              axes         = c(1, 2),
                              habillage    = df_clean$cluster_label,
                              addEllipses  = TRUE,
                              ellipse.type = "confidence",
                              geom.ind     = "point",
                              alpha.ind    = 0.3,
                              col.var      = "black",
                              label        = "var",
                              repel        = TRUE,
                              palette      = c("#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6"),
                              title        = "Biplot ACP + Clusters K-means") +
  theme_minimal()

ggsave("figures/15_biplot_acp_clusters.png", p_biplot, width = 11, height = 8)

# 9. RÉGRESSION LOGISTIQUE — Prédire la Victoire (Win) ------------------------

cat("\n--- Régression logistique (Win) ---\n")

df_logreg <- df_clean %>%
  select(Win, all_of(vars_num)) %>%
  mutate(Win = as.integer(Win))

set.seed(42)
idx_lr   <- createDataPartition(df_logreg$Win, p = 0.8, list = FALSE)
train_lr <- df_logreg[idx_lr, ]
test_lr  <- df_logreg[-idx_lr, ]

model_lr <- glm(Win ~ ., data = train_lr, family = binomial)
prob_lr  <- predict(model_lr, newdata = test_lr, type = "response")
pred_lr  <- ifelse(prob_lr > 0.5, 1L, 0L)
acc_lr   <- mean(pred_lr == test_lr$Win)

cat(sprintf("  Accuracy : %.1f%%\n", acc_lr * 100))

## 9.1 Coefficients (log-odds)
coef_df <- data.frame(
  variable = names(coef(model_lr))[-1],
  estimate = coef(model_lr)[-1]
) %>%
  mutate(direction = ifelse(estimate > 0, "Positif", "Négatif"))

p_coef <- ggplot(coef_df, aes(x = reorder(variable, estimate),
                               y = estimate, fill = direction)) +
  geom_col(show.legend = FALSE) +
  scale_fill_manual(values = c("Positif" = "#2ecc71", "Négatif" = "#e74c3c")) +
  coord_flip() +
  labs(title = sprintf("Régression logistique — Coefficients (Accuracy : %.1f%%)", acc_lr * 100),
       subtitle = "Variables prédictives de la victoire",
       x = NULL, y = "Coefficient (log-odds)") +
  theme_minimal()

ggsave("figures/16_logreg_coefficients.png", p_coef, width = 9, height = 6)

## 9.2 Matrice de confusion logistique
cm_lr_df <- as.data.frame(table(Prédit = pred_lr, Réel = test_lr$Win)) %>%
  mutate(Prédit = factor(Prédit, labels = c("Défaite", "Victoire")),
         Réel   = factor(Réel,   labels = c("Défaite", "Victoire")))

p_cm_lr <- ggplot(cm_lr_df, aes(x = Réel, y = Prédit, fill = Freq)) +
  geom_tile(color = "white") +
  geom_text(aes(label = Freq), size = 5, fontface = "bold") +
  scale_fill_gradient(low = "white", high = "#3498db") +
  labs(title = "Régression logistique — Matrice de confusion (Win)",
       fill = "N") +
  theme_minimal()

ggsave("figures/17_logreg_confusion.png", p_cm_lr, width = 6, height = 5)

# 10. RANDOM FOREST — Prédire la Lane -----------------------------------------

cat("\n--- Random Forest (Lane) ---\n")

df_rf <- df_clean %>%
  select(Lane, all_of(vars_num)) %>%
  mutate(Lane = factor(Lane))

set.seed(42)
idx_rf   <- createDataPartition(df_rf$Lane, p = 0.8, list = FALSE)
train_rf <- df_rf[idx_rf, ]
test_rf  <- df_rf[-idx_rf, ]

rf_model <- randomForest(Lane ~ ., data = train_rf, ntree = 300, importance = TRUE)
pred_rf  <- predict(rf_model, newdata = test_rf)
cm_rf    <- confusionMatrix(pred_rf, test_rf$Lane)

cat(sprintf("  Accuracy : %.1f%%\n", cm_rf$overall["Accuracy"] * 100))

## 10.1 Importance des variables
imp_df <- importance(rf_model) %>%
  as.data.frame() %>%
  tibble::rownames_to_column("variable") %>%
  arrange(desc(MeanDecreaseGini))

p_imp <- ggplot(imp_df, aes(x = reorder(variable, MeanDecreaseGini),
                              y = MeanDecreaseGini, fill = MeanDecreaseGini)) +
  geom_col(show.legend = FALSE) +
  scale_fill_gradient(low = "#d6eaf8", high = "#2471a3") +
  coord_flip() +
  labs(title = sprintf("Random Forest — Importance des variables (Accuracy : %.1f%%)",
                       cm_rf$overall["Accuracy"] * 100),
       subtitle = "Prédiction de la Lane à partir des stats de performance",
       x = NULL, y = "Mean Decrease Gini") +
  theme_minimal()

ggsave("figures/18_rf_importance.png", p_imp, width = 9, height = 6)

## 10.2 Matrice de confusion RF
cm_rf_df <- as.data.frame(cm_rf$table)

p_cm_rf <- ggplot(cm_rf_df, aes(x = Reference, y = Prediction, fill = Freq)) +
  geom_tile(color = "white") +
  geom_text(aes(label = Freq), size = 4, fontface = "bold") +
  scale_fill_gradient(low = "white", high = "#e74c3c") +
  labs(title = "Random Forest — Matrice de confusion (Lane)",
       x = "Réel", y = "Prédit", fill = "N") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))

ggsave("figures/19_rf_confusion.png", p_cm_rf, width = 8, height = 6)

cat("\n=== Analyse terminée. Figures dans figures/ | Tableaux dans output/ ===\n")
