---
name: vfp-bridge
description: >-
  Provides explanations, analogies, and code comparisons tailored for developers transitioning from Visual FoxPro 6 (VFP6 with .dbf tables) and basic Java Spring Boot to .NET 10, C#, EF Core, and Blazor in Mercacentro.
  Use this skill whenever explaining concepts, features, bugs, or architecture in this repository to the user.
---

# Skill: Explicador y Puente Conceptual (VFP6 & Spring Boot ➔ .NET 10 Mercacentro)

Esta skill define el estilo pedagógico y las equivalencias obligatorias para explicar cualquier concepto, arquitectura o fragmento de código de este proyecto al usuario.

---

## 1. Perfil del Desarrollador y Enfoque Pedagógico

- **Origen principal:** Programador experto en **Visual FoxPro 6 (VFP6)** trabajando con tablas libres (`.dbf` locales/red, sin motor cliente-servidor, manipulación directa de registros con puntero de tabla).
- **Conocimiento secundario:** Nivel básico en **Java Spring Boot** (conceptos de anotaciones `@RestController`, `@Service`, `@Repository`, DTOs).
- **Objetivo:** Comprender la solución **Mercacentro (.NET 10, C#, EF Core, Blazor)** sin saturarse de tecnicismos abstractos, usando comparaciones directas, sencillas y ejemplos prácticos.

---

## 2. Tabla Maestra de Equivalencias

| Concepto / Tarea | En Visual FoxPro 6 (VFP6) | En Java Spring Boot | En C# / .NET 10 (Mercacentro) |
| :--- | :--- | :--- | :--- |
| **Origen de datos** | Archivo físico `.dbf` en disco | Base de datos relacional (JPA/Hibernate) | PostgreSQL mapeado con **Entity Framework Core** |
| **Definir la estructura de datos** | Crear tabla / campos en Diseñador de Tablas | Clase `@Entity` | Clase en `Entities/` (hereda de `IBaseEntity`) |
| **Abrir tabla para consultar** | `USE Clientes IN 0` | `clienteRepository.findAll()` | `_context.Clientes.ToListAsync()` |
| **Buscar un registro por clave** | `SET ORDER TO TAG id`<br>`SEEK 123` o `LOCATE FOR id=123` | `clienteRepository.findById(123L)` | `_context.Clientes.FirstOrDefaultAsync(c => c.Id == 123)` |
| **Crear nuevo registro** | `APPEND BLANK`<br>`REPLACE Nombre WITH "Juan"` | `clienteRepo.save(new Cliente(...))` | `_context.Clientes.Add(nuevoCliente);`<br>`await _context.SaveChangesAsync();` |
| **Modificar registro** | `REPLACE Telefono WITH "555-1234"` | Modificar objeto y `save()` | Modificar propiedad y `await _context.SaveChangesAsync();` |
| **Borrado lógico (Soft Delete)** | `DELETE`<br>`SET DELETED ON` (ignora borrados)<br>`PACK` (limpieza física) | Campo `boolean deleted` manual o filtro Hibernate `@Where` | Automático en `AppDbContext`: intercepta borrado, pone `IsDeleted = true` y lo oculta con `HasQueryFilter` |
| **Multi-empresa (Multi-tenant)** | Carpeta separada por empresa con sus propios `.dbf` (`DATA_EMP1\`, `DATA_EMP2\`) | Filtros de tenant manuales / esquemas separados | Todo en la misma tabla con `TenantId`; `AppDbContext` filtra automáticamente solo los de la empresa actual (`JwtInfo.IdCompany`) |
| **Recorrer registros** | `SCAN ... ENDSCAN` | `for (Cliente c : lista)` | `foreach (var c in lista)` |
| **Pantalla / Interfaz Gráfica** | Formulario `.SCX` con controles nativos (Text, Grid) | Páginas HTML + Thymeleaf o SPA | Componente Blazor `.razor` con controles **Radzen Blazor** (Grid, DropDown, TextBox) |
| **Petición del cliente al servidor** | Acceso directo a disco / red compartida | Petición HTTP a un `@RestController` | Petición HTTP a un Controller (`[ApiController]`) vía `IRepository` |
| **Variables Globales / Entorno** | `PUBLIC gcUsuario, gnEmpresa` | `@Component` / Sesión de Spring | Inyección de Dependencias (`builder.Services.AddScoped...`) y `AsyncLocal` (`JwtInfo`) |

---

## 3. Estructura Obligatoria para Explicar Temas al Usuario

Cada vez que el usuario pregunte "cómo funciona X", "qué hace este código" o "cómo hago Y", la respuesta debe organizarse en este formato de 4 pasos:

### Paso 1: La Idea en Palabras Simples (Sin rodeos)
Explicar qué hace la funcionalidad con una analogía del mundo real o en lenguaje directo (máximo 2 a 3 oraciones).

### Paso 2: El Paralelo con FoxPro (VFP6)
Comparar directamente con cómo se resolvería en VFP6:
- *Ejemplo:* "En FoxPro abrías la tabla con `USE` y hacías un `LOCATE FOR`. Aquí no abres archivos a mano ni mueves un puntero de registro; le pides al motor PostgreSQL que te traiga el objeto ya filtrado."

### Paso 3: El Puente con Spring Boot (Si aplica y aclara)
Una breve referencia para conectar con su noción de Java:
- *Ejemplo:* "Esto equivale al `@RestController` que recibe el request y delega en el `@Service`."

### Paso 4: El Código en Mercacentro (.NET 10)
Mostrar el código real o ejemplo aplicable, con comentarios claros en español que expliquen qué hace cada línea.

---

## 4. Conceptos Clave de Mercacentro Explicados a estilo VFP6

1. **`Entities` y `AppDbContext` (Tu almacén de datos):**
   - En Fox tenías una carpeta con 20 archivos `.dbf`. En C#, `AppDbContext` representa toda tu base de datos y cada `DbSet<Cliente>` representa una tabla.
2. **`DTOs` (Data Transfer Objects):**
   - En Fox solías hacer un `SCATTER MEMVAR` o una tabla temporal `CURSOR` con solo 3 campos para mostrar en un Grid. En .NET, eso es un **DTO**: un paquetito con solo los datos necesarios para enviar entre el frontend y el backend sin mandar la tabla completa.
3. **`Async / Await`:**
   - En Fox la pantalla se congelaba mientras hacías un `REINDEX` o una consulta pesada en red. En .NET, `await` significa: *"ve haciendo la consulta a la base de datos de fondo y no congeles la pantalla del usuario"*.
4. **`Radzen Blazor`:**
   - Es el equivalente moderno a tu barra de herramientas de controles de VFP (los Grids interactivos con paginación, filtros automáticos, botones y cuadros de texto vinculados).
