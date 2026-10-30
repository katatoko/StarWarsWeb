using System.Text.Json.Serialization;

namespace DTOs
{
    public class CharacterDto
    {
        // se realiza esta correccion para que System.Text.Json no se confunda y pueda traducir correctamente cada campo de swapi
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("birth_year")]
        public string BirthYear { get; set; } = string.Empty;

        [JsonPropertyName("eye_color")]
        public string EyeColor { get; set; } = string.Empty;

        [JsonPropertyName("gender")]
        public string Gender { get; set; } = string.Empty;

        [JsonPropertyName("hair_color")]
        public string HairColor { get; set; } = string.Empty;

        [JsonPropertyName("height")]
        public string Height { get; set; } = string.Empty;

        [JsonPropertyName("mass")]
        public string Mass { get; set; } = string.Empty;

        [JsonPropertyName("skin_color")]
        public string SkinColor { get; set; } = string.Empty;

        [JsonPropertyName("homeworld")]
        public string Homeworld { get; set; } = string.Empty;

        [JsonPropertyName("films")]
        public List<string> Films { get; set; } = new();

        [JsonPropertyName("species")]
        public List<string> Species { get; set; } = new();

        [JsonPropertyName("starships")]
        public List<string> Starships { get; set; } = new();

        [JsonPropertyName("vehicles")]
        public List<string> Vehicles { get; set; } = new();

        [JsonPropertyName("url")]
        public string Url { get; set; } = string.Empty;

        [JsonPropertyName("created")]
        public string Created { get; set; } = string.Empty;

        [JsonPropertyName("edited")]
        public string Edited { get; set; } = string.Empty;
    }
}
