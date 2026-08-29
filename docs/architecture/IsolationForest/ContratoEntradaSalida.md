Contratos de Entrada y Salida

Para garantizar el trabajo en paralelo (Contract-First), el intellops-ai-engine consumirá y generará estrictamente los siguientes esquemas JSON.

Contrato de Entrada (Lectura de Batch)El pipeline leerá lotes de métricas procesadas, requiriendo el metric_type_id y el value como insumos primarios.  

JSON{
  "application_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "metric_id": "8bb38d38-9cb5-4521-8207-6cb5622a450a",
  "metric_type_id": 1, 
  "timestamp": "2026-08-28T21:15:00Z",
  "value": 1850.5,
  "session_count": 25
}


Contrato de Salida (Persistencia)Si se detecta una anomalía, el motor insertará transaccionalmente dos registros en la base de datos.

Registro en ANOMALY (Fase Matemática):

JSON{
  "anomaly_id": "a1b2c3d4-58cc-4372-a567-0e02b2c3d479",
  "metric_id": "8bb38d38-9cb5-4521-8207-6cb5622a450a",
  "model_id": "m9999999-58cc-4372-a567-0e02b2c3d479",
  "expected_value": 300.0,
  "actual_value": 1850.5,
  "severity_score": 0.89,
  "confidence_score": 0.95,
  "timestamp": "2026-08-28T21:16:05Z"
}

Registro en ALERT (Fase Semántica):

JSON{
  "alert_id": "b2c3d4e5-58cc-4372-a567-0e02b2c3d479",
  "anomaly_id": "a1b2c3d4-58cc-4372-a567-0e02b2c3d479",
  "recipient": "admin_gidas@utn.edu.ar",
  "channel_id": 1, 
  "message": "Se detectó una degradación crítica. El TTFB saltó a 1850.5ms cuando el comportamiento esperado era de 300.0ms.",
  "status_id": 1 
}