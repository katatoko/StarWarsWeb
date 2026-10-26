using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;

namespace DTOs
{
    public class SwapiResponseDto
    {
        //devuelve count por paginación, total de pjs
        [JsonPropertyName("count")]
        public int Count { get; set; }

        [JsonPropertyName("results")] 
        public List<CharacterDto> Results { get; set; } = new();

        [JsonPropertyName("next")]
        public string? Next { get; set; }

        [JsonPropertyName("previous")]
        public string? Previous { get; set; }
    }
}
