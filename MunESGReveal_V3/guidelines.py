"""
This file contains the list of guidelines (indicators) for municipal reporting.
Each guideline is represented as a dictionary with three keys:
  - Indicateur
  - Description
  - Dimension
"""

GUIDELINES = [
    {
        "Indicateur": "Politiques ou stratégies de développement durable",
        "Description": "Si la municipalité a une stratégie claire ou un plan d’action bien structuré, c’est un bon signe de proactivité. Si c’est juste mentionné en passant, c’est plus réactif.",
        "Dimension": "Gouvernance"
    },
    {
        "Indicateur": "Densité de la population urbaine",
        "Description": "S’ils parlent de densification, d’optimisation du territoire ou de mixité urbaine, c’est un geste planifié. Sinon, silence ou traitement passif.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Consommation d’eau",
        "Description": "Une municipalité proactive va avoir des données, des cibles ou des mesures concrètes pour réduire l’usage de l’eau. Une simple mention sans action, c’est moins engagé.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Empreinte écologique",
        "Description": "Parler d’empreinte écologique ou de bilan carbone avec des objectifs de réduction montre une vraie intention durable. Sinon, c’est flou ou absent.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Santé de la population",
        "Description": "Un diagnostic clair ou des actions liées à la santé des citoyen·ne·s, c’est un marqueur d’attention au bien-être collectif.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Transport en commun",
        "Description": "Un plan de transport collectif ou des cibles d’augmentation des usagers, c’est proactif. Sinon, ça reste au niveau des intentions.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Espaces naturels protégés",
        "Description": "Si la conservation de la biodiversité est planifiée avec des superficies ou des projets concrets, ça montre une vraie volonté environnementale.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Coût de la vie",
        "Description": "Une municipalité qui s’attaque à l’abordabilité (logement, services) en lien avec le développement durable démontre une approche équitable.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Taux d’activité",
        "Description": "Si on parle de participation active à l’économie locale avec des mesures pour l’emploi, c’est un signe de vitalité et de cohésion sociale.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Création d’emplois",
        "Description": "Mentionner la création d’emplois durables ou l’économie verte, c’est un plus du point de vue du développement durable.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Revenu des ménages",
        "Description": "Un suivi du revenu et des écarts de richesse montre une attention aux enjeux d’inégalités. S’il y a des objectifs ou des actions, c’est encore mieux.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Effort logement (30 % et +)",
        "Description": "Si le fardeau du logement est identifié et qu’il y a des solutions proposées, la ville est proactive socialement.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Niveau de scolarité",
        "Description": "Des données ou projets pour améliorer la formation de base ou continue, c’est une approche durable axée sur les capacités.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Taux de chômage",
        "Description": "Un traitement actif du chômage avec des programmes ou du soutien à l’emploi est un bon indicateur d’inclusion socioéconomique.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Inégalités de revenu",
        "Description": "Parler des écarts de revenu et chercher à les réduire est un geste clair vers une transition juste.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Aide sociale",
        "Description": "Une mention seule est faible, mais des actions pour diminuer la dépendance ou accompagner les personnes, c’est proactif.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Faibles revenus",
        "Description": "Identifier les ménages à faibles revenus et proposer des solutions démontre une vision sociale du développement durable.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Criminalité",
        "Description": "Aborder la sécurité de manière préventive ou communautaire est un signal positif pour un cadre de vie durable.",
        "Dimension": "Social"
    },
    {
        "Indicateur": "Participation électorale",
        "Description": "Une ville qui se soucie de la participation démocratique (et agit pour l’augmenter) est plus proactive en gouvernance.",
        "Dimension": "Gouvernance"
    },
    {
        "Indicateur": "Participation citoyenne",
        "Description": "Des mécanismes clairs, fréquents et ouverts de participation sont un excellent indicateur d’engagement durable.",
        "Dimension": "Gouvernance"
    },
    {
        "Indicateur": "Énergie renouvelable",
        "Description": "Si le document mentionne l’augmentation de l’énergie renouvelable ou des investissements dans ce sens, c’est clairement proactif.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Entreprises certifiées",
        "Description": "Une valorisation ou un accompagnement des entreprises vers des certifications environnementales, c’est une stratégie intelligente.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Recyclage (déchets détournés)",
        "Description": "Des taux de détournement élevés ou des plans d’amélioration montrent que la ville agit sur la réduction des déchets.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Particules PM10 (qualité de l’air)",
        "Description": "Si la qualité de l’air est suivie et que des mesures sont prises, la santé environnementale est prise au sérieux.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Émissions de GES (hors transport)",
        "Description": "Si la ville mesure, suit et agit sur les GES en dehors du transport, elle s’inscrit dans une vraie trajectoire de transition.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Bruit nocturne",
        "Description": "Mentionner le bruit, surtout nocturne, et proposer des mesures, c’est une marque de sensibilité à la qualité de vie.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Qualité des cours d’eau",
        "Description": "Des analyses de l’eau ou des projets de restauration ou de protection, c’est un engagement environnemental fort.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Déchets enfouis (résidentiels)",
        "Description": "Une baisse des déchets enfouis, appuyée par des plans d’action, montre que la gestion des matières résiduelles est prise au sérieux.",
        "Dimension": "Environnement"
    },
    {
        "Indicateur": "Activités sportives (parcs, piscines)",
        "Description": "L’accessibilité aux loisirs publics et leur fréquentation témoignent d’un souci de qualité de vie et de santé publique.",
        "Dimension": "Social"
    }
]
