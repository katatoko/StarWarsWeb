---
name: mercacentro-architecture
description: >-
  Explains the architecture, domain, backend microservices, frontends (Blazor WASM, MAUI, WinForms),
  multi-tenant isolation, security, and development conventions of the Mercacentro solution.
  Use this skill whenever working on, explaining, debugging, or adding features to the Mercacentro codebase.
---

# Mercacentro - Guía de Arquitectura y Funcionamiento del Proyecto

Este documento describe la arquitectura técnica, comportamiento del sistema, convenciones y patrones de diseño de la solución **Mercacentro**. Sirve como referencia contextual para cualquier modelo o desarrollador que opere sobre este repositorio.

---

## 1. Visión General del Proyecto

Mercacentro es una solución empresarial multi-plataforma y multi-tenant construida sobre **.NET 10** (`net10.0`), que integra:
- **Base de datos:** PostgreSQL gestionado mediante Entity Framework Core (`Npgsql.EntityFrameworkCore.PostgreSQL`).
- **Almacenamiento de archivos:** Soporte para MinIO y Azurite.
- **Múltiples clientes (Frontends):** Web (Blazor WebAssembly), Móvil (.NET MAUI Blazor Hybrid) y Escritorio (Windows Forms).
- **Backend Modular / Microservicios:** APIs REST especializadas (Auth, Security, Helper) con capas desacopladas de lógica, infraestructura y dominio.

---

## 2. Estructura de la Solución

```text
Mercacentro/
├── .agents/
│   └── skills/
│       └── mercacentro-architecture/
│           └── SKILL.md                 # Esta skill
├── 1.- Frontends/
│   ├── 1.1.- WebApp/                    # Blazor WebAssembly (.NET 10 + Radzen Blazor)
│   ├── 1.2.- MovilApp/                   # .NET MAUI Blazor Hybrid
│   └── 1.3.- DesktopApp/                # Windows Forms (.NET 10)
├── 2.- Backends/
│   ├── 2.1.- Microservices/             # APIs REST (Controllers, Hosting, Config)
│   │   ├── Auth.Api/                    # Autenticación, JWT, usuarios, perfiles
│   │   ├── Security.Api/                # Empresas, módulos, menús y permisos granulares
│   │   └── Helper.Api/                  # Almacenamiento de archivos y envío de correos
│   ├── 2.2.- Logic/                     # Capa de Lógica de Negocio (Servicios)
│   │   ├── Auth.Services/
│   │   ├── Security.Services/
│   │   └── Helper.Services/
│   ├── 2.3.- Infrastructure/            # Contratos de datos y persistencia
│   │   ├── Entities/                    # Modelos de base de datos e interfaces
│   │   └── DTOs/                        # Modelos de transferencia de datos
│   └── 2.4.- Domain/                    # AppDbContext, migraciones EF Core, Identity
├── Mercacentro.sln                      # Solución principal
├── Mercacentro.slnLaunch                # Perfil WeppAppAll para iniciar microservicios en paralelo
├── ENCODING_UTF8.md                     # Documentación de codificación obligatoria
└── .editorconfig                        # Reglas de estilo y UTF-8 con BOM
```

---

## 3. Comportamiento y Mecanismos Clave del Backend

### 3.1. Multi-Tenancy Dinámico (`ITenantScoped`)
- Las entidades asociadas a una empresa implementan `ITenantScoped` con la propiedad `TenantId` (`long?`).
- En `AppDbContext.OnModelCreating`, se inyecta un filtro de consulta global (`HasQueryFilter`) para todas las entidades que implementan `ITenantScoped`:
  ```csharp
  // _isDeveloper || e.TenantId == _tenantId
  ```
- **Aislamiento en tiempo de ejecución:** `CurrentTenantId` y `CurrentIsDeveloper` se evalúan dinámicamente mediante `JwtInfo` (con contexto aislado por request vía `AsyncLocal`). Si el usuario tiene rol o bandera de Developer, tiene bypass total y puede ver todos los tenants.
- Al crear nuevos registros (`Added`) en `SaveChangesAsync`, si la entidad implementa `ITenantScoped` y no tiene `TenantId`, se asigna automáticamente `JwtInfo.IdCompany`.

### 3.2. Auditoría y Soft Delete Automático (`IBaseEntity`)
- Las entidades del dominio implementan `IBaseEntity` (`Reference`, `IsActive`, `IsDeleted`, `CreatedAt`, `CreatedBy`, `UpdatedAt`, `UpdatedBy`, `DeletedAt`, `DeletedBy`).
- `AppDbContext.SaveChangesAsync` intercepta los cambios automáticamente:
  - **State == Added:** Asigna un nuevo `Reference` (GUID si es nulo), `CreatedAt` (`DateTime.UtcNow`), `CreatedBy` (`JwtInfo.IdUsuario`), `IsDeleted = false`, `IsActive = true`.
  - **State == Modified:** Actualiza `UpdatedAt` y `UpdatedBy`, protegiendo `CreatedAt` y `CreatedBy` de modificaciones.
  - **State == Deleted:** Intercepta la eliminación física y la transforma a borrado lógico:
    ```csharp
    entry.State = EntityState.Modified;
    entity.IsDeleted = true;
    entity.DeletedAt = DateTime.UtcNow;
    entity.DeletedBy = JwtInfo.IdUsuario;
    ```

### 3.3. Seguridad, Identidad y Permisos
- **ASP.NET Core Identity:** Personalizado para usar identificadores `long` (tablas `Users`, `Profiles`, `UserProfiles`, `UserClaims`, `UserLogins`, `RoleClaims`, `UserTokens`).
- **Tokens JWT:** Claves secretas y cifrado simétrico complementario AES (`EncryptionSettings`) configurados en `appsettings.json`.
- **Granularidad de Acceso:** Manejo jerárquico de **Empresas (`Companies`) -> Módulos (`Modulos`) -> Menús (`Menus`) -> Permisos (`Permisos`)**.

---

## 4. Comportamiento y Arquitectura del Frontend (WebApp)

- **Tecnología:** Blazor WebAssembly (.NET 10) con suite de UI **Radzen Blazor** (`DialogService`, `NotificationService`, `TooltipService`, etc.).
- **Autenticación en cliente:** `JWTAuthenticationProvider` gestiona el almacenamiento local de tokens, extracción de claims y notifica los cambios de estado a Blazor mediante `AuthenticationStateProvider`.
- **Contrato de Sesión:** Implementa la interfaz `ILoginService`:
  - Login y logout.
  - Almacenamiento y consulta de perfil y empresa activa.
  - Carga dinámica de menús y validación reactiva de permisos del usuario (`ValidarPermisos`).
- **Capa HTTP:** Consumo mediante `IRepository` / `Repository` encapsulando respuestas tipadas en `HttpResponseWrapper<T>`.

---

## 5. Reglas Críticas de Desarrollo y Convenciones

1. **Codificación Obligatoria (UTF-8 con BOM):**
   - Todos los archivos `.cs`, `.razor` y `.cshtml` **DEBEN** crearse y guardarse en **UTF-8 con BOM** (`EF BB BF`).
   - Esto evita corrupción de caracteres especiales (tildes, eñes) en Visual Studio y compiladores .NET.
2. **Nullable y Modern C#:**
   - La solución tiene `<Nullable>enable</Nullable>` activo. Manejar referencias nulas explícitamente sin warnings innecesarios.
3. **Persistencia mediante DTOs e Interfaces:**
   - No exponer entidades de persistencia directamente al cliente; utilizar los contratos en `2.3.- Infrastructure\DTOs`.
4. **Depuración de Microservicios:**
   - El archivo `Mercacentro.slnLaunch` define el perfil conjunto `WeppAppAll` para levantar en simultáneo `Auth.Api`, `Security.Api` y `Helper.Api`.
