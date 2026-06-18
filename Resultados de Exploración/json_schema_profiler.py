import json
import os
import hashlib
from collections import defaultdict, Counter
from tqdm import tqdm
import pandas as pd

# ==========================================================
# CONFIGURACION
# ==========================================================

JSON_FILE = "modulestore.structures.json"

MAX_EXAMPLES = 5
MAX_TOP_VALUES = 20

# ==========================================================
# ESTRUCTURAS
# ==========================================================

field_frequency = Counter()
field_types = defaultdict(Counter)
field_examples = defaultdict(set)

field_values = defaultdict(Counter)

schema_signatures = Counter()

total_documents = 0
invalid_documents = 0
max_depth_found = 0

# ==========================================================
# DETECCION DE TIPOS
# ==========================================================

def detect_type(value):

    if isinstance(value, dict):

        if "$oid" in value:
            return "ObjectId"

        if "$date" in value:
            return "Date"

        if "$numberLong" in value:
            return "Long"

        return "Object"

    if isinstance(value, list):
        return "Array"

    if isinstance(value, bool):
        return "Boolean"

    if isinstance(value, int):
        return "Integer"

    if isinstance(value, float):
        return "Float"

    if isinstance(value, str):
        return "String"

    if value is None:
        return "Null"

    return type(value).__name__

# ==========================================================
# RECORRIDO RECURSIVO
# ==========================================================

def traverse(obj, path="", depth=0):

    global max_depth_found

    max_depth_found = max(max_depth_found, depth)

    if isinstance(obj, dict):

        for k, v in obj.items():

            new_path = f"{path}.{k}" if path else k

            field_frequency[new_path] += 1

            t = detect_type(v)
            field_types[new_path][t] += 1

            if len(field_examples[new_path]) < MAX_EXAMPLES:
                try:
                    field_examples[new_path].add(str(v)[:150])
                except:
                    pass

            if isinstance(v, (str, int, float, bool)):
                field_values[new_path][str(v)] += 1

            traverse(v, new_path, depth + 1)

    elif isinstance(obj, list):

        array_path = path + "[]"

        field_frequency[array_path] += 1
        field_types[array_path]["Array"] += 1

        for item in obj:
            traverse(item, array_path, depth + 1)

# ==========================================================
# FIRMA DEL ESQUEMA
# ==========================================================

def extract_schema(obj):

    if isinstance(obj, dict):
        return {
            k: extract_schema(v)
            for k, v in sorted(obj.items())
        }

    if isinstance(obj, list):

        if not obj:
            return []

        return [extract_schema(obj[0])]

    return detect_type(obj)

# ==========================================================
# TAMANO DEL ARCHIVO
# ==========================================================

file_size = os.path.getsize(JSON_FILE)

print("\n==========================================")
print(" JSON SCHEMA PROFILER")
print("==========================================\n")

# ==========================================================
# PROCESAMIENTO
# ==========================================================

with open(JSON_FILE, "r", encoding="utf-8", errors="ignore") as f:

    with tqdm(
        total=file_size,
        unit="B",
        unit_scale=True,
        desc="Analizando"
    ) as pbar:

        while True:

            pos_before = f.tell()

            line = f.readline()

            if not line:
                break

            pbar.update(f.tell() - pos_before)

            line = line.strip()

            if not line:
                continue

            try:

                doc = json.loads(line)

                total_documents += 1

                traverse(doc)

                signature = json.dumps(
                    extract_schema(doc),
                    sort_keys=True
                )

                signature_hash = hashlib.md5(
                    signature.encode()
                ).hexdigest()

                schema_signatures[signature_hash] += 1

            except Exception:
                invalid_documents += 1

# ==========================================================
# DICCIONARIO DE DATOS
# ==========================================================

rows = []

for field in sorted(field_frequency.keys()):

    freq = field_frequency[field]

    pct = (
        (freq / total_documents) * 100
        if total_documents
        else 0
    )

    dominant_type = (
        field_types[field]
        .most_common(1)[0][0]
        if field_types[field]
        else "Unknown"
    )

    examples = " | ".join(
        list(field_examples[field])[:MAX_EXAMPLES]
    )

    rows.append({
        "Field": field,
        "Type": dominant_type,
        "Frequency": freq,
        "Percent": round(pct, 2),
        "Examples": examples
    })

dictionary_df = pd.DataFrame(rows)

# ==========================================================
# TOP VALUES
# ==========================================================

value_rows = []

for field, values in field_values.items():

    for value, count in values.most_common(MAX_TOP_VALUES):

        value_rows.append({
            "Field": field,
            "Value": value,
            "Count": count
        })

values_df = pd.DataFrame(value_rows)

# ==========================================================
# ESQUEMAS
# ==========================================================

schema_rows = []

for signature, count in schema_signatures.most_common():

    schema_rows.append({
        "SchemaHash": signature,
        "Documents": count
    })

schema_df = pd.DataFrame(schema_rows)

# ==========================================================
# EXPORTACIONES
# ==========================================================

dictionary_df.to_csv(
    "diccionario_datos.csv",
    index=False
)

values_df.to_csv(
    "top_values.csv",
    index=False
)

schema_df.to_csv(
    "schema_signatures.csv",
    index=False
)

with pd.ExcelWriter(
    "diccionario_datos.xlsx",
    engine="openpyxl"
) as writer:

    dictionary_df.to_excel(
        writer,
        sheet_name="Diccionario",
        index=False
    )

    values_df.to_excel(
        writer,
        sheet_name="TopValues",
        index=False
    )

    schema_df.to_excel(
        writer,
        sheet_name="Schemas",
        index=False
    )

# ==========================================================
# RESUMEN
# ==========================================================

with open(
    "resumen.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write("====================================\n")
    f.write("RESUMEN DEL ANALISIS\n")
    f.write("====================================\n\n")

    f.write(
        f"Documentos validos: {total_documents}\n"
    )

    f.write(
        f"Documentos invalidos: {invalid_documents}\n"
    )

    f.write(
        f"Campos detectados: {len(field_frequency)}\n"
    )

    f.write(
        f"Profundidad maxima: {max_depth_found}\n"
    )

    f.write(
        f"Esquemas distintos: {len(schema_signatures)}\n"
    )

print("\n==========================================")
print(" ANALISIS FINALIZADO")
print("==========================================")
print(f"Documentos: {total_documents:,}")
print(f"Campos: {len(field_frequency):,}")
print(f"Profundidad maxima: {max_depth_found}")
print(f"Esquemas distintos: {len(schema_signatures):,}")

print("\nArchivos generados:")
print(" - diccionario_datos.csv")
print(" - diccionario_datos.xlsx")
print(" - top_values.csv")
print(" - schema_signatures.csv")
print(" - resumen.txt")