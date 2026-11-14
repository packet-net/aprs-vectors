# Clean live packets to add as observed cases (from aprs-watch, 2026-11-14)

Each decodes in all six libraries at v1.1.0 with no diagnostics, lenient and strict, and re-encodes identical or equivalent. Source `APRS-IS 2026-11-14`. Share is the shape's share of live packets that day (3.6M).

1. plain `=` position with a comment, 4.27%: `EA5AKC-6>APDW19,WIDE1-1,WIDE2-2,qAO,EA5ILC-10:=3823.68N/00031.43W` <San Vicente> QRV: <145.225 & C4FM 07575 >`
2. course, speed, altitude, comment, 1.68%: `SM6OEQ-7>APRS-7,WIDE2-1,qAR,SK6QA-10:!5802.78N/01137.08E[232/000/A=000167Anytone D878UVII`
3. messaging, altitude, comment, 0.79%: `DO5RW-5>APRS,TCPIP*,qAC,T2FMNETZ:=5038.29N/00714.16E[/A=000459TG53639 FM 145.225 QRV`
4. timestamp, course, speed, altitude, comment, 0.77%: `ZS4OIL-19>APCLEY,TCPIP*,qAC,APRS-ZA:/141020z2642.77S/02753.23Ev150/028/A=004753 50C 1Mv 4.19V In 14.34V  70kmh`
5. course, speed, comment, 0.72%: `E25RIV-9>APDW16,TCPIP*,qAC,T2INDY:!1322.38NP10100.11E>000/000Toyota Yaris Ativ | Stanby 145.7250MHz -- Num SAT : 11`
6. timestamp, messaging, altitude, comment, 0.70%: `BD7LMA-15>APOSB4,TCPIP*,qAS,BD7LMA:@141019z2302.55N/11303.90E0/A=000000SharkRF openSPOT4`
7. compressed, comment, base-91 telemetry, 0.51%: `9W2SQ-3>APLRG1,WIDE1-1,qAO,9M2OCX-2:!LLq1Dh45L#  GLoRa APRS Digipeater 433.400mhz @ Bukit Dinding Kuala Lumpur|+U%I|`
8. h timestamp, messaging, course, speed, altitude, comment, 0.28%: `BG7JD-3>APLM3D,TCPIP*,qAC,T2TOKYO:@102010h2258.99N\11319.02Ek328/020/A=000075Mobile iGate(144.640MHz 1200bps) 07_13.3V`
9. timestamp, weather, 0.18%: `N2UFM-13>APWW11,WIDE1-1,WIDE2-1,qAS,N2UFM-1:/140520z4032.37N/07410.18W_348/002g012t039r000p035P000h77b10085`
10. course, speed, altitude, no comment, 0.17%: `HS6PFB-9>AESPT4,TCPIP*,qAC,APRSTH:!1424.40N/10052.77Ef356/004/A=000042`
11. messaging, frequency, comment, 0.16%: `SQ5AZ-1>APRS,TCPIP*,qAS,SQ5AZ:=5212.50N/02058.06E-145.500MHz or SR5W`
12. compressed, altitude, comment, 0.15%: `OH1SA-12>APLRT1,WIDE1-1,Q1287,qAR,OH1RDS:!//pqAT(+m[=(Q Bat=4.12V ( 0mA)`
13. messaging, course, speed, 0.14%: `KE7FGR-2>APN000,TCPIP*,qAC,T2MCI:=4003.45N\11139.85W)285/002`
14. compressed, nothing else, 0.09%: `S58GM-9>APLRT1,WIDE1-1,qAR,S53BL-10:!/75X/R.ly> gQ`
