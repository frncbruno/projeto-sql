import pandas as pd

df = pd.read_csv("data/raw/Colegios_santa_maria_raw.csv")

# Indicadores e pesos
basico      = ["IN_AGUA_POTAVEL", "IN_ENERGIA_REDE_PUBLICA", "IN_ESGOTO_REDE_PUBLICA",
               "IN_LIXO_SERVICO_COLETA", "IN_BANHEIRO", "IN_COZINHA"]

pedagogico  = ["IN_BIBLIOTECA", "IN_LABORATORIO_CIENCIAS", "IN_LABORATORIO_INFORMATICA",
               "IN_QUADRA_ESPORTES", "IN_SALA_PROFESSOR", "IN_REFEITORIO", "IN_PATIO_COBERTO"]

tecnologia  = ["IN_INTERNET", "IN_BANDA_LARGA", "IN_COMPUTADOR", "IN_EQUIP_MULTIMIDIA"]

acesso      = ["IN_ACESSIBILIDADE_RAMPAS", "IN_ACESSIBILIDADE_CORRIMAO", "IN_ACESSIBILIDADE_PISOS_TATEIS"]
penalidade  = ["IN_ACESSIBILIDADE_INEXISTENTE"]

extras      = ["IN_AUDITORIO", "IN_BANHEIRO_PNE", "IN_BANHEIRO_CHUVEIRO",
               "IN_SALA_DIRETORIA", "IN_SECRETARIA"]

# Cálculo do score bruto (máximo 36 pontos)
df["IIE_BRUTO"] = (
    df[basico].fillna(0).sum(axis=1) * 1 +
    df[pedagogico].fillna(0).sum(axis=1) * 2 +
    df[tecnologia].fillna(0).sum(axis=1) * 2 +
    df[acesso].fillna(0).sum(axis=1) * 1 -
    df[penalidade].fillna(0).sum(axis=1) * 2 +
    df[extras].fillna(0).sum(axis=1) * 1
)

# Normalização para 0–100
df["IIE"] = ((df["IIE_BRUTO"] - df["IIE_BRUTO"].min()) /
             (df["IIE_BRUTO"].max() - df["IIE_BRUTO"].min()) * 100).round(1)

# Classificação por categoria (cortes definidos em 61,1 e 75,0)
def classificar(iie):
    if iie >= 75.0:
        return "Boa"
    elif iie >= 61.1:
        return "Mediana"
    else:
        return "Precária"

df["CAT_INFRA"] = df["IIE"].apply(classificar)

# Exportar resultado
df[["CO_ENTIDADE", "NO_ENTIDADE", "IIE", "CAT_INFRA"]].to_csv("outputs/infra_scores.csv", index=False)

print(df["CAT_INFRA"].value_counts())
