<?php
declare(strict_types=1);

$errors = [];
$output = null;

function valid_domain(string $value): bool {
    return (bool) preg_match('/^(?!-)([A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,63}$/', $value);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $domain = trim((string) ($_POST['domain'] ?? ''));
    $matrix = trim((string) ($_POST['matrix'] ?? ''));
    $brand = trim((string) ($_POST['brand'] ?? 'CallChat'));

    if (!valid_domain($domain)) {
        $errors[] = 'Enter a valid public domain.';
    }
    if (strpos($matrix, 'https://') !== 0) {
        $errors[] = 'Matrix API URL must start with https://';
    }
    if ($brand === '') {
        $errors[] = 'Brand name is required.';
    }

    if (!$errors) {
        $matrixHost = preg_replace('#^https://#', '', rtrim($matrix, '/'));
        $output = [
            'client' => json_encode(['m.homeserver' => ['base_url' => rtrim($matrix, '/')]], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES),
            'server' => json_encode(['m.server' => $matrixHost . ':443'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES),
            'element' => json_encode([
                'default_server_config' => [
                    'm.homeserver' => [
                        'base_url' => rtrim($matrix, '/'),
                        'server_name' => $domain,
                    ],
                ],
                'brand' => $brand,
                'disable_guests' => true,
                'default_theme' => 'dark',
            ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES),
            'env' => "SERVER_NAME={$domain}\nPUBLIC_BASEURL=" . rtrim($matrix, '/') . "/\nSYNAPSE_REPORT_STATS=no\nPOSTGRES_DB=synapse\nPOSTGRES_USER=synapse\nPOSTGRES_PASSWORD=CHANGE_ME_LONG_RANDOM_VALUE\n",
        ];
    }
}
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CallChat Setup Builder</title>
  <link rel="stylesheet" href="../../web/public/assets/style.css">
  <style>textarea{width:100%;min-height:140px;border:1px solid var(--line);border-radius:12px;background:#071219;color:var(--text);padding:14px;font:14px/1.5 ui-monospace,monospace}.form-grid{display:grid;gap:14px}.form-grid input{width:100%;padding:14px;border:1px solid var(--line);border-radius:10px;background:#071219;color:var(--text)}.error{color:#ffd761}</style>
</head>
<body>
  <main class="narrow">
    <h1>CallChat Setup Builder</h1>
    <p class="lead">Generate safe public config files for a Matrix-compatible CallChat deployment. This page does not ask for real passwords or write to your server.</p>
    <?php foreach ($errors as $error): ?><p class="error"><?php echo htmlspecialchars($error); ?></p><?php endforeach; ?>
    <form method="post" class="form-grid">
      <label>Public domain <input name="domain" value="<?php echo htmlspecialchars($_POST['domain'] ?? 'example.com'); ?>"></label>
      <label>Matrix API URL <input name="matrix" value="<?php echo htmlspecialchars($_POST['matrix'] ?? 'https://matrix.example.com'); ?>"></label>
      <label>Brand name <input name="brand" value="<?php echo htmlspecialchars($_POST['brand'] ?? 'CallChat'); ?>"></label>
      <button class="primary" type="submit">Generate Config</button>
    </form>
    <?php if ($output): ?>
      <h2>.well-known/matrix/client</h2><textarea readonly><?php echo htmlspecialchars($output['client']); ?></textarea>
      <h2>.well-known/matrix/server</h2><textarea readonly><?php echo htmlspecialchars($output['server']); ?></textarea>
      <h2>Element config.json</h2><textarea readonly><?php echo htmlspecialchars($output['element']); ?></textarea>
      <h2>infra/synapse/.env starter</h2><textarea readonly><?php echo htmlspecialchars($output['env']); ?></textarea>
    <?php endif; ?>
  </main>
</body>
</html>
