using StarWars.Services;

var builder = WebApplication.CreateBuilder(args);

// Controladores y Swagger con Annotations
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.EnableAnnotations();
});

// Registrar cliente HTTP de Star Wars
builder.Services.AddHttpClient<SwapiService>();

var app = builder.Build();

// Interfaz visual de Swagger
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
