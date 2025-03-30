-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: 26.03.2025 klo 21:15
-- Palvelimen versio: 8.0.41-cll-lve
-- PHP Version: 8.3.19

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `gabpmkse_books`
--

-- --------------------------------------------------------

--
-- Rakenne taululle `books`
--

CREATE TABLE `books` (
  `id` int NOT NULL,
  `isbn` varchar(13) COLLATE utf8mb4_general_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'EMPTY',
  `author_last` varchar(255) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'EMPTY',
  `author_first` varchar(255) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'EMPTY',
  `year` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Vedos taulusta `books`
--

INSERT INTO `books` (`id`, `isbn`, `title`, `author_last`, `author_first`, `year`) VALUES
(1, '9516113656', 'Purjehdus Bysanttiin', 'Silverberg', 'Robert', 1990),
(2, '9516113672', 'Kujanjuoksu', 'Zelazny', 'Roger', 1990),
(3, '9516114067', 'Aikakoneen saaga', 'Harrison', 'Harry', 1991),
(4, '9516114075', 'Vaeltaja', 'Leiber', 'Fritz', 1993),
(7, '9510134473', 'Säätiö', 'Asimov', 'Isaac', 1986),
(19, '9789511484257', 'Fingerpori / 17', 'Jarla', 'Pertti', 2024),
(20, '9789512329694', 'Alkumetsä', 'Holdstock', 'Robert', 1991),
(21, '9789520100964', 'Aikaloukku', 'Vinge', 'Vernor', 2008),
(22, '9789518954258', 'Top science fiction / 1', 'Pachter', 'Josh', 1990),
(23, '9789516114074', 'Vaeltaja', 'Leiber', 'Fritz', 1993),
(24, '9789516116399', 'YHTEYKSIÄ', 'WATSON', 'IAN', 1993),
(25, '9789516116979', 'Yösiivet', 'Silverberg', 'Robert', 1994),
(26, '9789516118799', 'Viimeisten aikojen valtiaat', 'Moorcock', 'Michael', 1997),
(27, '9789512059294', 'Galaksin kansalainen', 'Heinlein', 'Robert A.', 2001);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `books`
--
ALTER TABLE `books`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `books`
--
ALTER TABLE `books`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
