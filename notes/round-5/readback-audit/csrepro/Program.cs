using Packet.Aprs;

// 1. Weather extra fields are written unchecked (no read-back): they read back as standard fields.
var ts = AprsTimestamp.MonthDayHoursMinutes(10, 9, 23, 45);
foreach (var (l, v) in new[] { ('#', "123"), ('h', "50"), ('A', "A00"), ('t', "077") })
{
    var w = new AprsWeather { PressureMillibars = 1013.2, AdditionalFields = [new AprsWeatherField(l, v)] };
    foreach (AprsData d in new AprsData[] {
        new AprsWeatherReport { Timestamp = ts, Weather = w },
        new AprsPositionReport { Position = new AprsPosition(51.5, -0.5), Symbol = AprsSymbol.Parse("/_"), Weather = w },
        new AprsPositionReport { Position = new AprsPosition(51.5, -0.5), Symbol = AprsSymbol.Parse("/_"), Weather = w with { SoftwareType = 'w', UnitType = "RSW" } } })
    {
        try
        {
            var p = AprsPacket.Create("N0CALL", d);
            var back = AprsPacket.Decode(p.ToTnc2());
            var bw = back.Data switch { AprsWeatherReport r => r.Weather, AprsPositionedData q => q.Weather, _ => null };
            Console.WriteLine($"{p}\n   same={back.Data == d} extras={bw?.AdditionalFields.Count} raw={bw?.RainRawCounter} hum={bw?.HumidityPercent} sw={bw?.SoftwareType}{bw?.UnitType} diags={string.Join(",", back.Diagnostics.Select(x => x.Code))}");
        }
        catch (AprsEncodeException e) { Console.WriteLine($"refused {e.Code}"); }
    }
}

// 2. Header: a path entry not marked used, before one that is, reads back marked used.
var hp = AprsPacket.Create(AprsAddress.Parse("N0CALL"), new AprsStatusReport { Text = "hi" }, null,
    [new AprsPathEntry(AprsAddress.Parse("WIDE1-1"), false), new AprsPathEntry(AprsAddress.Parse("N0CALL-1"), true)]);
var hb = AprsPacket.Decode(hp.ToTnc2());
Console.WriteLine($"{hp}\n   path[0] given used=False, reads back used={hb.Path[0].Used}");
