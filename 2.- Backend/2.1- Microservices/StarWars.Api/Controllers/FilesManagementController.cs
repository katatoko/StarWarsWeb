using Domain;
using Entities;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StarWars.Domain;
using Swashbuckle.AspNetCore.Annotations;

namespace StarWars.Api.Controllers
{
    [SwaggerTag("Administra las imágenes de los personajes.")]
    [Route("api/[controller]")]
    public class FilesManagementController(AppDbContext db) : ControllerBase
    {
        [HttpPost("upload")]
        [Consumes("multipart/form-data")]
        [SwaggerOperation(Summary = "Sube y asocia una imagen a un personaje.")]
        [RequestSizeLimit(10 * 1024 * 1024)]
        public async Task<IActionResult> Upload(IFormFile file, [FromForm] long characterId)
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest("Debe seleccionar un archivo válido.");
            }

            if (characterId <= 0)
            {
                return BadRequest("Debe especificar un ID de personaje válido.");
            }

            using var memoryStream = new MemoryStream();
            await file.CopyToAsync(memoryStream);
            // Si ya tenía una foto previa, la actualizamos; si no, creamos una nueva
            var imagenExistente = await db.CharacterImages.FirstOrDefaultAsync(img => img.CharacterId == characterId);
            if (imagenExistente != null)
            {
                imagenExistente.FileName = file.FileName;
                imagenExistente.ContentType = file.ContentType;
                imagenExistente.Data = memoryStream.ToArray();
                imagenExistente.CreatedAt = DateTime.UtcNow;
            }
            else
            {
                var nuevaImagen = new CharacterImage
                {
                    CharacterId = characterId,
                    FileName = file.FileName,
                    ContentType = file.ContentType,
                    Data = memoryStream.ToArray()
                };
                db.CharacterImages.Add(nuevaImagen);
            }
            await db.SaveChangesAsync();
            return Ok(new { message = "Imagen guardada correctamente en la base de datos." });
        }

        //GET api/FilesManagement/{characterId} Muestra la imagen
        [HttpGet("{characterId}")]
        [SwaggerOperation(Summary = "Obtiene la imagen de un personaje por su ID.")]
        public async Task<IActionResult> GetImage(long characterId)
        {
            var imagen = await db.CharacterImages.FirstOrDefaultAsync(img => img.CharacterId == characterId);
            if (imagen == null)
            {
                return NotFound("El personaje no tiene imagen personalizada.");
            }
            return File(imagen.Data, imagen.ContentType);
        }
    }
}
