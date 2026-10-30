# Instructivo: análisis estático de Mercacentro

Genera un informe PDF con la calidad del código (nota de A a E) y un CSV con cada hallazgo, para que revises tu propio código.

## 1. Requisitos (una sola vez)

- SDK de .NET 10 (`dotnet --version` debe mostrar 10.x).
- Python 3.10 o superior (`python --version`). Al instalarlo, marca **Add Python to PATH**.
- Las librerías de Python:

  ```powershell
  python -m pip install matplotlib reportlab
  ```

## 2. Copiar la carpeta

El instructor te entrega la carpeta `analisis-estatico`. Cópiala dentro de tu repositorio, en `docs\`:

```
D:\GitHub\Mercacentro\docs\analisis-estatico\
    analisis_estatico.py
    ejecutar.ps1
    INSTRUCTIVO.md
```

La carpeta `docs\` está excluida de Git, así que no aparecerá en tus commits.

## 3. Preparar el código

1. Cierra Visual Studio o detén las APIs que tengas corriendo, porque bloquean los archivos de `bin\`.
2. Ubícate en la rama que quieres medir (la tuya o `develop`) y actualízala:

   ```powershell
   cd D:\GitHub\Mercacentro
   git checkout <tu-rama>
   git pull
   ```

El análisis mide los archivos tal como están en tu disco, incluidos los cambios sin commit.

## 4. Ejecutar

Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File docs\analisis-estatico\ejecutar.ps1
```

Tarda unos minutos y muestra tres pasos: limpiar, compilar y generar el informe. Durante la compilación es normal ver avisos de licencia de **NPOI** o **SixLabors**; no afectan el resultado.

## 5. Revisar los resultados

Los archivos quedan en `docs\analisis-estatico\`:

| Archivo | Para qué sirve |
|---|---|
| `Informe-Analisis-Estatico-Mercacentro.pdf` | Nota general, puntuación por dimensión, hallazgos y recomendaciones |
| `hallazgos.csv` | Lista completa de hallazgos con archivo y línea; ábrela en Excel y filtra por los archivos que tocaste |

Cada ejecución sobrescribe el informe y el CSV. Si quieres compararlos después de corregir algo, cópialos antes a otra carpeta.

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| `No module named 'matplotlib'` o `'reportlab'` | Repite el `pip install` del paso 1 |
| `python no se reconoce...` | Reinstala Python marcando *Add to PATH*, o usa `py` en lugar de `python` |
| `The process cannot access the file...` | Hay una API o Visual Studio abiertos: ciérralos y vuelve a ejecutar |
| `FileNotFoundError: advertencias-compilador.txt` | Ejecutaste el `.py` directamente; usa `ejecutar.ps1` |
| La nota sale muy baja y casi todo son errores de compilación | Tu rama no compila: corrige primero los errores en Visual Studio |
