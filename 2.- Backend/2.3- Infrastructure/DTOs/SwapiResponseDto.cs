using System;
using System.Collections.Generic;
using System.Text;

namespace DTOs
{
    public class SwapiResponseDto
    {
        //devuelve count por paginación, total de pjs
        public int Count { get; set; }
        public List<CharacterDto> Results { get; set; }
    }
}
