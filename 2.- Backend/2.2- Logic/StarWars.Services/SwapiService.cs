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
        public async Task<List<CharacterDto>> GetCharactersAsync()
        {
            var respuesta = await httpCli.GetFromJsonAsync<SwapiResponseDto>("https://swapi.dev/api/people/");

            if (respuesta == null)
            {
                return new List<CharacterDto>();
            }

            return respuesta.Results;
        }

        // Consulta por id de personaje
        public async Task<CharacterDto?> GetCharacterByIdAsync(string id)
        {
            return await httpCli.GetFromJsonAsync<CharacterDto>($"https://swapi.dev/api/people/{id}/");
        }
    }
}
