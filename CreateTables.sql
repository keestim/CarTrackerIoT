CREATE TABLE Journeys (
  journeyID INT UNSIGNED NOT NULL AUTO_INCREMENT,
  startLatitude FLOAT(4),
  startLongitude FLOAT(4),
  startTime DATETIME NOT NULL,
  PRIMARY KEY (`journeyID`)
);

CREATE TABLE JourneyDetails(
  journeyID INT UNSIGNED NOT NULL,
  latitude FLOAT(4),
  longitude FLOAT(4),
  speed INT,
  RPM INT,
  gear INT,
  FOREIGN KEY (`journeyID`) REFERENCES Journeys(`journeyID`)
);

CREATE TABLE SpeedingOccurances (
  journeyID INT UNSIGNED NOT NULL,
  occuranceTime DATETIME,
  speed INT,
  speedLimit INT,
  RPM INT,
  FOREIGN KEY (`journeyID`) REFERENCES Journeys(`journeyID`)
);
