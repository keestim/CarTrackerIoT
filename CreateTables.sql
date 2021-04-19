CREATE DATABASE CarTrackingData;

USE CarTrackingData;

CREATE TABLE Journeys (
  journeyID INT UNSIGNED NOT NULL AUTO_INCREMENT,
  startLatitude FLOAT(4),
  startLongitude FLOAT(4),
  startTime DATETIME NOT NULL,
  PRIMARY KEY (`journeyID`)
);

CREATE TABLE JourneyDetails (
  journeyInstanceID INT UNSIGNED NOT NULL AUTO_INCREMENT,
  journeyID INT UNSIGNED NOT NULL,
  latitude FLOAT(4),
  longitude FLOAT(4),
  speed INT,
  RPM INT,
  time DATETIME NOT NULL,
  PRIMARY KEY (`journeyInstanceID`)
  FOREIGN KEY (`journeyID`) REFERENCES Journeys(`journeyID`)
);

CREATE TABLE SpeedingOccurances (
  speedingOccuranceID INT UNSIGNED NOT NULL AUTO_INCREMENT,
  journeyID INT UNSIGNED NOT NULL,
  occuranceTime DATETIME,
  speed INT,
  speedLimit INT,
  RPM INT,
  time DATETIME NOT NULL,
  PRIMARY KEY (`speedingOccuranceID`)
  FOREIGN KEY (`journeyID`) REFERENCES Journeys(`journeyID`)
);