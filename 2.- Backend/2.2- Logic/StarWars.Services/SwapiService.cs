using System;
using System.Collections.Generic;
using System.Text;
using System.Net.Http.Json;
using DTOs;

namespace StarWars.Services
{
    public class SwapiService(HttpClient httpCli)
    {

        //Consulta general de personajes
        public async Task<SwapiResponseDto> GetCharactersAsync(int page = 1)
        {
            //var respuesta = await httpCli.GetFromJsonAsync<SwapiResponseDto>("https://swapi.dev/api/people/");

            // el campo next entrega la url con la siguiente pagina en cada consulta, de ahi se extrae la url
            var respuesta = await httpCli.GetFromJsonAsync<SwapiResponseDto>($"https://swapi.dev/api/people/?page={page}");

            if (respuesta == null)
            {
                return new SwapiResponseDto();
            }

            return respuesta;
        }

        // Consulta por id de personaje
        public async Task<CharacterDto?> GetCharacterByIdAsync(string id)
        {
            return await httpCli.GetFromJsonAsync<CharacterDto>($"https://swapi.dev/api/people/{id}/");
        }
    }
}
