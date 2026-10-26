using DTOs;
using Microsoft.AspNetCore.Mvc;
using StarWars.Services;
using Swashbuckle.AspNetCore.Annotations;

namespace StarWars.Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [SwaggerTag("Muestra información de los personajes de Star Wars.")]
    public class CharacterController(SwapiService swapiService) : ControllerBase
    {
        [HttpGet("Personajes")]
        [SwaggerOperation(Summary = "Obtiene la lista general de personajes.")]
        public async Task<ActionResult<SwapiResponseDto>> GetAll([FromQuery] int page = 1)
        {
            var resultado = await swapiService.GetCharactersAsync(page);
            return Ok(resultado);
        }

        [HttpGet("{id}")]
        [SwaggerOperation(Summary = "Obtiene el detalle de un personaje por su ID.")]
        public async Task<ActionResult<CharacterDto>> GetById(string id)
        {
            var personaje = await swapiService.GetCharacterByIdAsync(id);
            if (personaje == null)
            {
                return NotFound("Personaje no encontrado.");
            }
            return Ok(personaje);
        }
    }
}
