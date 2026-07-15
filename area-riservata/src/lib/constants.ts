export const Ruoli = ["ADMIN", "ASSOCIATO", "OSSERVATORE", "CONSIGLIO"] as const;
export type Ruolo = (typeof Ruoli)[number];

export const StatiPresenza = ["PRESENTE", "ASSENTE", "IN_DUBBIO", "NON_RISPOSTO"] as const;
export type StatoPresenza = (typeof StatiPresenza)[number];

export const TipiEvento = ["RADUNO", "RTO", "ALLENAMENTO", "SEZIONALE", "DESIGNAZIONE", "ALTRO"] as const;
export const TipiNotifica = ["DESIGNAZIONE", "RTO", "EVENTO", "DOCUMENTO", "NEWS", "CONVOCAZIONE", "MESSAGGIO", "GENERALE"] as const;
export const TipiPreferito = ["DOCUMENTO", "QUIZ", "RTO", "MEDIA", "VIDEO"] as const;
export const TipiDocumento = ["FILE_RTO", "SLIDE", "VIDEO", "QUIZ", "REGOLAMENTO", "CIRCOLARE", "TEST_TECNICO"] as const;
